from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone

from src.core import models
from src.services.dashboard import DashboardService
from src.services.debt import filter_debts_for_month
from src.services.month_closing import MonthClosingService


class MonthClosingServiceTests(TestCase):
    def setUp(self):
        self.owner = models.User.objects.create_user(
            username="month_owner",
            password="pass123",
        )
        self.branch = models.Branch.objects.create(
            name="Main Branch",
            owner=self.owner,
        )
        self.phone_category = models.PhoneCategory.objects.create(name="Smartphones")
        self.accessory_category = models.AccessoryCategory.objects.create(name="Cases")

        self.current_month = timezone.localdate().replace(day=1)
        self.reference_time = timezone.make_aware(
            datetime(self.current_month.year, self.current_month.month, 1, 0, 1, 0),
            timezone.get_current_timezone(),
        )
        self.period = MonthClosingService.resolve_period(self.reference_time)

        self.previous_month_dt = timezone.make_aware(
            datetime(
                self.period["closing_month"].year,
                self.period["closing_month"].month,
                15,
                12,
                0,
                0,
            ),
            timezone.get_current_timezone(),
        )
        self.current_month_dt = timezone.make_aware(
            datetime(
                self.current_month.year,
                self.current_month.month,
                10,
                12,
                0,
                0,
            ),
            timezone.get_current_timezone(),
        )

    def _set_model_values(self, instance, **values):
        instance.__class__.all_objects.filter(pk=instance.pk).update(**values)
        instance.refresh_from_db()
        return instance

    def _create_phone(
        self,
        *,
        branch=None,
        imei="IMEI-001",
        cost_price=Decimal("500.00"),
        sell_price=None,
        is_sold=False,
        sold_at=None,
        added_at=None,
        sold_by=None,
    ):
        phone = models.Phone.objects.create(
            name="Phone",
            category=self.phone_category,
            branch=branch or self.branch,
            imei=imei,
            storage="128",
            color="Black",
            from_by="Supplier",
            cost_price=cost_price,
            sell_price=sell_price,
            is_sold=is_sold,
            added_by=self.owner,
            sold_by=sold_by,
            sold_at=sold_at,
        )
        timestamp = added_at or self.previous_month_dt
        self._set_model_values(
            phone,
            added_at=timestamp,
            updated_at=timestamp,
            sold_at=sold_at,
        )
        return phone

    def _create_accessory(
        self,
        *,
        branch=None,
        name="Case",
        stock=3,
        unit_cost=Decimal("20.00"),
        added_at=None,
    ):
        accessory = models.Accessory.objects.create(
            name=name,
            category=self.accessory_category,
            branch=branch or self.branch,
            unit_cost=unit_cost,
            stock=stock,
            added_by=self.owner,
        )
        timestamp = added_at or self.previous_month_dt
        self._set_model_values(
            accessory,
            added_at=timestamp,
            updated_at=timestamp,
        )
        return accessory

    def _create_debt(self, *, added_at=None, remaining_amount=Decimal("100.00")):
        debt = models.Debt.objects.create(
            branch=self.branch,
            created_by=self.owner,
            f_name="Debt Person",
            amount=Decimal("150.00"),
            remaining_amount=remaining_amount,
            direction="WE_GAVE",
            domain=models.Debt.DOMAIN_PHONE,
            note="Monthly debt",
        )
        timestamp = added_at or self.previous_month_dt
        self._set_model_values(
            debt,
            added_at=timestamp,
            updated_at=timestamp,
        )
        return debt

    def _close_branch(self, *, dry_run=False):
        return MonthClosingService.close_branch(
            branch=self.branch,
            closing_month=self.period["closing_month"],
            next_month_start=self.period["next_month_start"],
            previous_month_end_dt=self.period["previous_month_end_dt"],
            next_month_start_dt=self.period["next_month_start_dt"],
            dry_run=dry_run,
            batch_size=1,
        )

    def test_close_branch_leaves_unsold_phone_unchanged(self):
        phone = self._create_phone()
        original_added_at = phone.added_at

        result = self._close_branch()

        phone.refresh_from_db()
        self.assertFalse(result.skipped)
        self.assertEqual(result.snapshot_action, "created")
        # rollover marks old phone as closed and creates one new phone for next month
        self.assertEqual(models.Phone.objects.count(), 2)
        self.assertFalse(phone.is_sold)
        self.assertIsNone(phone.sold_at)
        self.assertIsNone(phone.sell_price)
        self.assertEqual(phone.added_at, original_added_at)
        self.assertTrue(phone.is_month_closed)
        self.assertIsNotNone(phone.month_closed_at)
        new_phone = models.Phone.objects.get(rolled_over_from=phone)
        self.assertFalse(new_phone.is_sold)
        self.assertFalse(new_phone.is_month_closed)

    def test_close_branch_leaves_accessory_stock_and_sales_unchanged(self):
        accessory = self._create_accessory(stock=4, unit_cost=Decimal("15.00"))
        original_added_at = accessory.added_at

        self._close_branch()

        accessory.refresh_from_db()
        self.assertEqual(models.AccessorySale.objects.filter(branch=self.branch).count(), 0)
        self.assertEqual(accessory.stock, 4)
        self.assertEqual(accessory.added_at, original_added_at)

    def test_close_branch_does_not_change_capitals(self):
        phone_capital = models.PhoneCapital.objects.create(
            branch=self.branch,
            month=self.period["closing_month"],
            invested_amount=Decimal("1000.00"),
            current_balance=Decimal("400.00"),
        )
        accessory_capital = models.AccessoryCapital.objects.create(
            branch=self.branch,
            month=self.period["closing_month"],
            invested_amount=Decimal("700.00"),
            current_balance=Decimal("200.00"),
        )

        self._close_branch()

        phone_capital.refresh_from_db()
        accessory_capital.refresh_from_db()
        self.assertEqual(phone_capital.invested_amount, Decimal("1000.00"))
        self.assertEqual(phone_capital.current_balance, Decimal("400.00"))
        self.assertEqual(accessory_capital.invested_amount, Decimal("700.00"))
        self.assertEqual(accessory_capital.current_balance, Decimal("200.00"))

    def test_close_branch_does_not_copy_or_adjust_debts(self):
        debt = self._create_debt(remaining_amount=Decimal("80.00"))
        payment = models.DebtPayment.objects.create(
            debt=debt,
            amount=Decimal("20.00"),
            remaining_balance=Decimal("80.00"),
            paid_by=self.owner,
            note="partial payment",
        )
        self._set_model_values(
            payment,
            added_at=self.previous_month_dt,
            updated_at=self.previous_month_dt,
        )

        self._close_branch()

        debt.refresh_from_db()
        payment.refresh_from_db()
        self.assertEqual(models.Debt.objects.count(), 1)
        self.assertEqual(models.DebtPayment.objects.count(), 1)
        self.assertEqual(
            filter_debts_for_month(
                models.Debt.objects.filter(branch=self.branch),
                self.period["closing_month"],
            ).count(),
            1,
        )
        self.assertEqual(
            filter_debts_for_month(
                models.Debt.objects.filter(branch=self.branch),
                self.period["next_month_start"],
            ).count(),
            0,
        )
        self.assertEqual(debt.remaining_amount, Decimal("80.00"))
        self.assertEqual(payment.amount, Decimal("20.00"))

    def test_close_all_branches_creates_snapshots_for_every_branch(self):
        second_branch = models.Branch.objects.create(
            name="Second Branch",
            owner=self.owner,
        )
        self._create_phone(imei="MAIN-001")
        self._create_phone(branch=second_branch, imei="SECOND-001")

        results = list(
            MonthClosingService.close_all_branches(
                reference_time=self.reference_time,
                batch_size=1,
            )
        )

        self.assertEqual(len(results), 2)
        self.assertEqual(
            models.DashboardSnapshot.objects.filter(month=self.period["closing_month"]).count(),
            2,
        )
        self.assertTrue(
            models.DashboardSnapshot.objects.filter(
                branch=self.branch,
                month=self.period["closing_month"],
            ).exists()
        )
        self.assertTrue(
            models.DashboardSnapshot.objects.filter(
                branch=second_branch,
                month=self.period["closing_month"],
            ).exists()
        )

    def test_close_branch_is_idempotent_when_snapshot_exists(self):
        self._create_phone()

        first_result = self._close_branch()
        second_result = self._close_branch()

        self.assertEqual(first_result.snapshot_action, "created")
        self.assertTrue(second_result.skipped)
        self.assertEqual(second_result.snapshot_action, "skipped")
        self.assertEqual(
            models.DashboardSnapshot.objects.filter(
                branch=self.branch,
                month=self.period["closing_month"],
            ).count(),
            1,
        )
        self.assertEqual(
            models.MonthClosingRecord.objects.filter(
                branch=self.branch,
                month=self.period["closing_month"],
            ).count(),
            1,
        )

    def test_close_branch_dry_run_does_not_persist_snapshot_or_record(self):
        phone = self._create_phone()
        accessory = self._create_accessory()

        result = self._close_branch(dry_run=True)

        phone.refresh_from_db()
        accessory.refresh_from_db()
        self.assertIn(result.snapshot_action, {"would_create", "would_update", "would_skip"})
        self.assertFalse(phone.is_sold)
        self.assertIsNone(phone.sold_at)
        self.assertEqual(accessory.stock, 3)
        self.assertFalse(
            models.MonthClosingRecord.objects.filter(
                branch=self.branch,
                month=self.period["closing_month"],
            ).exists()
        )
        self.assertFalse(
            models.DashboardSnapshot.objects.filter(
                branch=self.branch,
                month=self.period["closing_month"],
            ).exists()
        )

    def test_close_branch_failure_marks_record_failed_without_mutations(self):
        phone = self._create_phone()
        accessory = self._create_accessory(stock=2)
        original_phone_added_at = phone.added_at
        original_accessory_added_at = accessory.added_at

        with self.assertRaises(RuntimeError):
            with patch.object(
                MonthClosingService,
                "_persist_dashboard_snapshot",
                side_effect=RuntimeError("snapshot write failed"),
            ):
                self._close_branch()

        phone.refresh_from_db()
        accessory.refresh_from_db()
        self.assertFalse(phone.is_sold)
        self.assertIsNone(phone.sold_at)
        self.assertEqual(phone.added_at, original_phone_added_at)
        self.assertEqual(accessory.stock, 2)
        self.assertEqual(accessory.added_at, original_accessory_added_at)
        self.assertFalse(models.DashboardSnapshot.objects.filter(branch=self.branch).exists())

        closing_record = models.MonthClosingRecord.objects.get(
            branch=self.branch,
            month=self.period["closing_month"],
        )
        self.assertEqual(closing_record.status, models.MonthClosingRecord.STATUS_FAILED)

    def test_dashboard_returns_snapshot_for_past_month_and_live_for_current_month(self):
        past_phone = self._create_phone(
            imei="PAST-SOLD-001",
            is_sold=True,
            cost_price=Decimal("500.00"),
            sell_price=Decimal("800.00"),
            sold_at=self.previous_month_dt,
            sold_by=self.owner,
            added_at=self.previous_month_dt - timedelta(days=5),
        )
        current_phone = self._create_phone(
            imei="CURRENT-SOLD-001",
            is_sold=True,
            cost_price=Decimal("450.00"),
            sell_price=Decimal("700.00"),
            sold_at=self.current_month_dt,
            sold_by=self.owner,
            added_at=self.current_month_dt - timedelta(days=2),
        )

        self._close_branch()
        models.Phone.all_objects.filter(pk=past_phone.pk).update(sell_price=Decimal("9999.00"))
        past_phone.refresh_from_db()
        current_phone.refresh_from_db()

        past_dashboard = DashboardService.get_phone_dashboard(
            branch=self.branch,
            year=self.period["closing_month"].year,
            month=self.period["closing_month"].month,
        )
        current_dashboard = DashboardService.get_phone_dashboard(
            branch=self.branch,
            year=self.current_month.year,
            month=self.current_month.month,
        )

        self.assertTrue(past_dashboard["from_snapshot"])
        self.assertEqual(past_dashboard["phone_profit"], 300.0)
        self.assertEqual(current_dashboard["phone_profit"], Decimal("250.00"))
