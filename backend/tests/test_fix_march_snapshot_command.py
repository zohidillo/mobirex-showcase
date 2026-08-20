from datetime import datetime
from decimal import Decimal
from io import StringIO

from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone

from src.core import models


class FixMarchSnapshotCommandTests(TestCase):
    def setUp(self):
        self.owner = models.User.objects.create_user(
            username="march_owner",
            password="pass123",
        )
        self.branch = models.Branch.objects.create(
            name="March Branch",
            owner=self.owner,
        )
        self.phone_category = models.PhoneCategory.objects.create(name="Smartphones")
        self.month_start = datetime(2026, 3, 1).date()
        self.timezone = timezone.get_current_timezone()

    def _set_model_values(self, instance, **values):
        instance.__class__.all_objects.filter(pk=instance.pk).update(**values)
        instance.refresh_from_db()
        return instance

    def _aware(self, year, month, day, hour=0, minute=0, second=0):
        return timezone.make_aware(
            datetime(year, month, day, hour, minute, second),
            self.timezone,
        )

    def _create_phone(
        self,
        *,
        name="Phone",
        imei,
        cost_price,
        sell_price=None,
        is_sold=False,
        sold_at=None,
        added_at=None,
        sold_by=None,
        for_month_close=False,
    ):
        phone = models.Phone.objects.create(
            name=name,
            category=self.phone_category,
            branch=self.branch,
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
            for_month_close=for_month_close,
        )
        timestamp = added_at or self._aware(2026, 3, 10, 12, 0, 0)
        self._set_model_values(
            phone,
            added_at=timestamp,
            updated_at=timestamp,
            sold_at=sold_at,
        )
        return phone

    def test_command_repairs_existing_march_snapshot_without_mutating_phones(self):
        artificial_sold_at = self._aware(2026, 3, 31, 23, 59, 59)
        recreated_added_at = self._aware(2026, 4, 1, 0, 0, 0)

        original_phone = self._create_phone(
            imei="ARTIFICIAL-001",
            cost_price=Decimal("500.00"),
            sell_price=Decimal("500.00"),
            is_sold=True,
            sold_at=artificial_sold_at,
            added_at=self._aware(2026, 3, 12, 11, 0, 0),
            sold_by=None,
        )
        recreated_phone = self._create_phone(
            imei="ARTIFICIAL-001",
            cost_price=Decimal("500.00"),
            is_sold=False,
            added_at=recreated_added_at,
            for_month_close=True,
        )
        real_sale = self._create_phone(
            imei="REAL-001",
            cost_price=Decimal("300.00"),
            sell_price=Decimal("450.00"),
            is_sold=True,
            sold_at=self._aware(2026, 3, 20, 15, 30, 0),
            added_at=self._aware(2026, 3, 5, 9, 0, 0),
            sold_by=self.owner,
        )

        models.DashboardSnapshot.objects.create(
            branch=self.branch,
            month=self.month_start,
            dashboard_data={"stale": True},
            phone_data={"stale": True},
            accessory_data={},
            debt_data={},
            expense_data={},
            salary_data={},
            capital_data={},
            is_locked=False,
        )

        stdout = StringIO()
        call_command(
            "fix_march_snapshot",
            "--month",
            "2026-03",
            stdout=stdout,
        )

        snapshot = models.DashboardSnapshot.objects.get(
            branch=self.branch,
            month=self.month_start,
        )
        phone_data = snapshot.phone_data
        dashboard_data = snapshot.dashboard_data

        self.assertTrue(snapshot.is_locked)
        self.assertNotIn("stale", phone_data)
        self.assertEqual(phone_data["phones_sold_count"], 1)
        self.assertEqual(phone_data["phone_profit"], 150.0)
        self.assertEqual(phone_data["total_sold_value"], 450.0)
        self.assertEqual(phone_data["phones_remaining_count"], 1)
        self.assertEqual(phone_data["remaining_value"], 500.0)
        self.assertEqual(phone_data["sales_series"], [{"day": 20, "amount": 450.0}])

        self.assertEqual(dashboard_data["profit_summary"]["phone_profit"], 150.0)
        self.assertEqual(dashboard_data["profit_summary"]["net_profit"], 150.0)
        self.assertEqual(dashboard_data["inventory_summary"]["phones_sold_count"], 1)
        self.assertEqual(dashboard_data["inventory_summary"]["phones_available_count"], 1)
        self.assertEqual(
            dashboard_data["last_transactions"],
            [
                {
                    "type": "PHONE_SALE",
                    "object_id": real_sale.id,
                    "amount": 450.0,
                    "profit": 150.0,
                    "occurred_at": real_sale.sold_at.isoformat(),
                }
            ],
        )

        original_phone.refresh_from_db()
        recreated_phone.refresh_from_db()
        self.assertTrue(original_phone.is_sold)
        self.assertEqual(original_phone.sold_at, artificial_sold_at)
        self.assertEqual(original_phone.sell_price, Decimal("500.00"))
        self.assertTrue(recreated_phone.for_month_close)
        self.assertFalse(recreated_phone.is_sold)
        self.assertEqual(models.Phone.all_objects.count(), 3)

        output = stdout.getvalue()
        self.assertIn(f"Branch #{self.branch.id} {self.branch.name}", output)
        self.assertIn("detected=1", output)
        self.assertIn("excluded_sales=1", output)
        self.assertIn("snapshot=updated", output)

    def test_dry_run_reports_detected_phones_without_writing_snapshot(self):
        self._create_phone(
            imei="ARTIFICIAL-DRY-001",
            cost_price=Decimal("700.00"),
            sell_price=Decimal("700.00"),
            is_sold=True,
            sold_at=self._aware(2026, 3, 31, 23, 59, 59),
            added_at=self._aware(2026, 3, 18, 10, 0, 0),
            sold_by=None,
        )
        recreated_phone = self._create_phone(
            imei="ARTIFICIAL-DRY-001",
            cost_price=Decimal("700.00"),
            is_sold=False,
            added_at=self._aware(2026, 4, 1, 0, 0, 0),
            for_month_close=True,
        )

        stdout = StringIO()
        call_command(
            "fix_march_snapshot",
            "--month",
            "2026-03",
            "--dry-run",
            stdout=stdout,
        )

        recreated_phone.refresh_from_db()
        self.assertFalse(
            models.DashboardSnapshot.objects.filter(
                branch=self.branch,
                month=self.month_start,
            ).exists()
        )
        self.assertTrue(recreated_phone.for_month_close)

        output = stdout.getvalue()
        self.assertIn(f"Branch #{self.branch.id} {self.branch.name}", output)
        self.assertIn("detected=1", output)
        self.assertIn("excluded_sales=1", output)
        self.assertIn("snapshot=would_create", output)
