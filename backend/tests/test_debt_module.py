from decimal import Decimal
from datetime import datetime, timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from src.core import models
from src.services.debt import (
    DebtCreateService,
    DebtPaymentCreateService,
    DebtPaymentDeleteService,
    DebtPaymentUpdateService,
)


class DebtModuleViewTests(TestCase):
    def setUp(self):
        self.owner = models.User.objects.create_user(username="owner", password="pass123")
        self.branch = models.Branch.objects.create(name="Main Branch", owner=self.owner)
        models.BranchUser.objects.create(
            user=self.owner,
            branch=self.branch,
            role=models.BranchUser.ROLE_OWNER,
        )
        self.phone_seller = models.User.objects.create_user(
            username="phone_seller", password="pass123"
        )
        models.BranchUser.objects.create(
            user=self.phone_seller,
            branch=self.branch,
            role=models.BranchUser.ROLE_PHONE_SELLER,
        )
        self.client.force_login(self.owner)

    def _create_phone_capital(self, amount=Decimal("1000")):
        month_start = timezone.now().date().replace(day=1)
        return models.PhoneCapital.objects.create(
            branch=self.branch,
            month=month_start,
            invested_amount=amount,
            current_balance=amount,
        )

    def _set_added_at(self, instance, value):
        instance.__class__.all_objects.filter(pk=instance.pk).update(
            added_at=value,
            updated_at=value,
        )
        instance.refresh_from_db()

    def test_main_debt_list_shows_only_unpaid_and_partially_paid_debts(self):
        unpaid = models.Debt.objects.create(
            branch=self.branch,
            created_by=self.owner,
            f_name="Unpaid Person",
            amount=Decimal("100"),
            remaining_amount=Decimal("100"),
            direction="WE_GAVE",
        )
        partial = models.Debt.objects.create(
            branch=self.branch,
            created_by=self.owner,
            f_name="Partial Person",
            amount=Decimal("200"),
            remaining_amount=Decimal("50"),
            direction="WE_TOOK",
        )
        fully_paid = models.Debt.objects.create(
            branch=self.branch,
            created_by=self.owner,
            f_name="Paid Person",
            amount=Decimal("300"),
            remaining_amount=Decimal("0"),
            direction="WE_GAVE",
        )
        models.DebtPayment.objects.create(
            debt=fully_paid,
            amount=Decimal("300"),
            remaining_balance=Decimal("0"),
            paid_by=self.owner,
            note="Closed",
        )

        response = self.client.get(reverse("debt_list"))

        self.assertEqual(response.status_code, 200)
        object_ids = {obj.id for obj in response.context["object_list"]}
        self.assertIn(unpaid.id, object_ids)
        self.assertIn(partial.id, object_ids)
        self.assertNotIn(fully_paid.id, object_ids)
        self.assertContains(response, "To‘lovlarni ko‘rish")

    def test_create_payment_stores_historical_remaining_balance(self):
        self._create_phone_capital()
        debt = DebtCreateService.create_debt(
            branch=self.branch,
            f_name="History Test",
            amount=Decimal("1000"),
            direction="WE_GAVE",
            created_by=self.phone_seller,
            note="History",
        )

        payment_1 = DebtPaymentCreateService.create_payment(
            debt=debt,
            amount=Decimal("200"),
            paid_by=self.owner,
            note="Birinchi to‘lov",
        )
        debt.refresh_from_db()
        payment_2 = DebtPaymentCreateService.create_payment(
            debt=debt,
            amount=Decimal("300"),
            paid_by=self.owner,
            note="Ikkinchi to‘lov",
        )
        debt.refresh_from_db()

        self.assertEqual(payment_1.remaining_balance, Decimal("800"))
        self.assertEqual(payment_2.remaining_balance, Decimal("500"))
        self.assertEqual(debt.remaining_amount, Decimal("500"))

    def test_creating_current_month_debt_only_changes_its_own_month_capital(self):
        month_start = timezone.localdate().replace(day=1)
        if month_start.month == 12:
            next_month = month_start.replace(year=month_start.year + 1, month=1)
        else:
            next_month = month_start.replace(month=month_start.month + 1)

        current_capital = models.PhoneCapital.objects.create(
            branch=self.branch,
            month=month_start,
            invested_amount=Decimal("1000"),
            current_balance=Decimal("1000"),
        )
        next_capital = models.PhoneCapital.objects.create(
            branch=self.branch,
            month=next_month,
            invested_amount=Decimal("500"),
            current_balance=Decimal("500"),
        )

        DebtCreateService.create_debt(
            branch=self.branch,
            f_name="Own Month Capital",
            amount=Decimal("120"),
            direction="WE_GAVE",
            created_by=self.phone_seller,
            note="Isolation",
        )

        current_capital.refresh_from_db()
        next_capital.refresh_from_db()

        self.assertEqual(current_capital.current_balance, Decimal("880"))
        self.assertEqual(next_capital.current_balance, Decimal("500"))

    def test_payment_delete_and_recreate_recalculates_remaining_from_all_active_payments(self):
        self._create_phone_capital()
        debt = DebtCreateService.create_debt(
            branch=self.branch,
            f_name="Consistency Test",
            amount=Decimal("10"),
            direction="WE_GAVE",
            created_by=self.phone_seller,
            note="Consistency",
        )

        first_payment = DebtPaymentCreateService.create_payment(
            debt=debt,
            amount=Decimal("5"),
            paid_by=self.owner,
            note="Birinchi to‘lov",
        )
        second_payment = DebtPaymentCreateService.create_payment(
            debt=debt,
            amount=Decimal("3"),
            paid_by=self.owner,
            note="Ikkinchi to‘lov",
        )

        DebtPaymentDeleteService.delete_payment(second_payment, self.owner)
        debt.refresh_from_db()
        first_payment.refresh_from_db()
        second_payment.refresh_from_db()

        self.assertTrue(second_payment.is_deleted)
        self.assertEqual(first_payment.remaining_balance, Decimal("5"))
        self.assertEqual(debt.remaining_amount, Decimal("5"))

        final_payment = DebtPaymentCreateService.create_payment(
            debt=debt,
            amount=Decimal("5"),
            paid_by=self.owner,
            note="Yakuniy to‘lov",
        )
        debt.refresh_from_db()
        first_payment.refresh_from_db()
        final_payment.refresh_from_db()

        self.assertEqual(first_payment.remaining_balance, Decimal("5"))
        self.assertEqual(final_payment.remaining_balance, Decimal("0"))
        self.assertEqual(debt.remaining_amount, Decimal("0"))

    def test_payment_update_recalculates_remaining_balances_in_order(self):
        self._create_phone_capital()
        debt = DebtCreateService.create_debt(
            branch=self.branch,
            f_name="Update Test",
            amount=Decimal("10"),
            direction="WE_GAVE",
            created_by=self.phone_seller,
            note="Update",
        )
        first_payment = DebtPaymentCreateService.create_payment(
            debt=debt,
            amount=Decimal("6"),
            paid_by=self.owner,
            note="Birinchi",
        )
        second_payment = DebtPaymentCreateService.create_payment(
            debt=debt,
            amount=Decimal("2"),
            paid_by=self.owner,
            note="Ikkinchi",
        )

        DebtPaymentUpdateService.update_payment(
            second_payment,
            {"amount": Decimal("4"), "note": "Yangilandi"},
            self.owner,
        )
        debt.refresh_from_db()
        first_payment.refresh_from_db()
        second_payment.refresh_from_db()

        self.assertEqual(first_payment.remaining_balance, Decimal("4"))
        self.assertEqual(second_payment.remaining_balance, Decimal("0"))
        self.assertEqual(debt.remaining_amount, Decimal("0"))

    def test_paid_debt_list_filters_by_selected_month_using_debt_creation_date(self):
        now = timezone.now()
        last_month = (now.replace(day=1) - timedelta(days=1)).replace(
            hour=10,
            minute=0,
            second=0,
            microsecond=0,
        )

        paid_last_month = models.Debt.objects.create(
            branch=self.branch,
            created_by=self.owner,
            f_name="Last Month Paid",
            amount=Decimal("150"),
            remaining_amount=Decimal("0"),
            direction="WE_GAVE",
        )
        self._set_added_at(paid_last_month, last_month)
        first_payment = models.DebtPayment.objects.create(
            debt=paid_last_month,
            amount=Decimal("50"),
            remaining_balance=Decimal("100"),
            paid_by=self.owner,
            note="First part",
        )
        final_payment = models.DebtPayment.objects.create(
            debt=paid_last_month,
            amount=Decimal("100"),
            remaining_balance=Decimal("0"),
            paid_by=self.owner,
            note="Final part",
        )
        self._set_added_at(first_payment, last_month)
        self._set_added_at(final_payment, now)

        paid_this_month = models.Debt.objects.create(
            branch=self.branch,
            created_by=self.owner,
            f_name="Current Month Paid",
            amount=Decimal("220"),
            remaining_amount=Decimal("0"),
            direction="WE_TOOK",
        )
        current_payment = models.DebtPayment.objects.create(
            debt=paid_this_month,
            amount=Decimal("220"),
            remaining_balance=Decimal("0"),
            paid_by=self.owner,
            note="Closed now",
        )
        self._set_added_at(current_payment, now)

        partial = models.Debt.objects.create(
            branch=self.branch,
            created_by=self.owner,
            f_name="Still Open",
            amount=Decimal("180"),
            remaining_amount=Decimal("20"),
            direction="WE_GAVE",
        )
        models.DebtPayment.objects.create(
            debt=partial,
            amount=Decimal("160"),
            remaining_balance=Decimal("20"),
            paid_by=self.owner,
            note="Partial",
        )

        response = self.client.get(
            reverse("debt_paid_list"),
            {"year": str(now.year), "month": str(now.month)},
        )

        self.assertEqual(response.status_code, 200)
        object_ids = {obj.id for obj in response.context["object_list"]}
        self.assertIn(paid_this_month.id, object_ids)
        self.assertNotIn(paid_last_month.id, object_ids)
        self.assertNotIn(partial.id, object_ids)
        self.assertContains(response, "Current Month Paid")
        self.assertNotContains(response, "Last Month Paid")
        self.assertContains(response, "Closed now")

        last_month_response = self.client.get(
            reverse("debt_paid_list"),
            {"year": str(last_month.year), "month": str(last_month.month), "history_mode": "full"},
        )
        last_month_ids = {obj.id for obj in last_month_response.context["object_list"]}
        self.assertIn(paid_last_month.id, last_month_ids)
        self.assertNotIn(paid_this_month.id, last_month_ids)
        self.assertContains(last_month_response, "First part")
        self.assertContains(last_month_response, "Final part")

        search_response = self.client.get(
            reverse("debt_paid_list"),
            {"q": "Current"},
        )
        search_ids = {obj.id for obj in search_response.context["object_list"]}
        self.assertEqual(search_ids, {paid_this_month.id})

    def test_deleting_debt_soft_deletes_related_payments(self):
        self._create_phone_capital()

        debt = DebtCreateService.create_debt(
            branch=self.branch,
            f_name="Delete Me",
            amount=Decimal("120"),
            direction="WE_GAVE",
            created_by=self.phone_seller,
            note="Will be deleted",
        )
        payment = DebtPaymentCreateService.create_payment(
            debt=debt,
            amount=Decimal("20"),
            paid_by=self.owner,
            note="Partial payment",
        )

        confirm_response = self.client.get(reverse("debt_delete", args=[debt.pk]))
        self.assertContains(
            confirm_response,
            "Ushbu qarz va unga bog‘liq barcha to‘lovlar o‘chiriladi.",
        )

        response = self.client.post(reverse("debt_delete", args=[debt.pk]))

        self.assertEqual(response.status_code, 302)
        debt.refresh_from_db()
        payment.refresh_from_db()
        self.assertTrue(debt.is_deleted)
        self.assertTrue(payment.is_deleted)
        self.assertEqual(
            models.DebtPayment.objects.filter(debt=debt).count(),
            0,
        )
        self.assertEqual(
            models.DebtPayment.all_objects.filter(debt=debt, is_deleted=True).count(),
            1,
        )

    def test_past_month_debt_cannot_be_deleted_or_paid(self):
        current_month = timezone.localdate().replace(day=1)
        previous_month = current_month - timedelta(days=1)
        previous_month_dt = timezone.make_aware(
            datetime(previous_month.year, previous_month.month, 18, 10, 0, 0)
        )

        past_debt = models.Debt.objects.create(
            branch=self.branch,
            created_by=self.owner,
            f_name="Past Debt",
            amount=Decimal("100"),
            remaining_amount=Decimal("100"),
            direction="WE_GAVE",
        )
        self._set_added_at(past_debt, previous_month_dt)

        list_response = self.client.get(
            reverse("debt_list"),
            {"year": str(previous_month.year), "month": str(previous_month.month)},
        )
        self.assertEqual(list_response.status_code, 200)
        self.assertContains(list_response, "Past Debt")
        self.assertNotContains(list_response, reverse("debt_delete", args=[past_debt.pk]))

        delete_response = self.client.get(reverse("debt_delete", args=[past_debt.pk]))
        self.assertEqual(delete_response.status_code, 302)
        past_debt.refresh_from_db()
        self.assertFalse(past_debt.is_deleted)

        payment_response = self.client.post(
            reverse("debt_payment_create"),
            {"branch": self.branch.id, "debt": past_debt.id, "amount": "10", "note": "Blocked"},
        )
        self.assertEqual(payment_response.status_code, 200)
        self.assertFalse(
            models.DebtPayment.objects.filter(
                debt=past_debt,
                note="Blocked",
                is_deleted=False,
            ).exists()
        )

    def test_debt_payment_list_filters_by_debt_month_and_is_read_only_for_past_month(self):
        current_month = timezone.localdate().replace(day=1)
        previous_month = current_month - timedelta(days=1)
        previous_month_dt = timezone.make_aware(
            datetime(previous_month.year, previous_month.month, 18, 10, 0, 0)
        )
        current_month_dt = timezone.make_aware(
            datetime(current_month.year, current_month.month, 5, 10, 0, 0)
        )

        previous_debt = models.Debt.objects.create(
            branch=self.branch,
            created_by=self.owner,
            f_name="Previous Debt",
            amount=Decimal("200"),
            remaining_amount=Decimal("100"),
            direction="WE_GAVE",
        )
        current_debt = models.Debt.objects.create(
            branch=self.branch,
            created_by=self.owner,
            f_name="Current Debt",
            amount=Decimal("150"),
            remaining_amount=Decimal("100"),
            direction="WE_GAVE",
        )
        self._set_added_at(previous_debt, previous_month_dt)
        self._set_added_at(current_debt, current_month_dt)

        previous_month_payment = models.DebtPayment.objects.create(
            debt=previous_debt,
            amount=Decimal("40"),
            remaining_balance=Decimal("160"),
            paid_by=self.owner,
            note="Previous month payment",
        )
        current_month_payment_on_previous_debt = models.DebtPayment.objects.create(
            debt=previous_debt,
            amount=Decimal("60"),
            remaining_balance=Decimal("100"),
            paid_by=self.owner,
            note="Current month payment on old debt",
        )
        current_debt_payment = models.DebtPayment.objects.create(
            debt=current_debt,
            amount=Decimal("50"),
            remaining_balance=Decimal("100"),
            paid_by=self.owner,
            note="Current debt payment",
        )
        self._set_added_at(previous_month_payment, previous_month_dt)
        self._set_added_at(current_month_payment_on_previous_debt, current_month_dt)
        self._set_added_at(current_debt_payment, current_month_dt)

        previous_response = self.client.get(
            reverse("debt_payment_list"),
            {"year": str(previous_month.year), "month": str(previous_month.month)},
        )
        self.assertEqual(previous_response.status_code, 200)
        previous_ids = {obj.id for obj in previous_response.context["object_list"]}
        self.assertIn(previous_month_payment.id, previous_ids)
        self.assertIn(current_month_payment_on_previous_debt.id, previous_ids)
        self.assertNotIn(current_debt_payment.id, previous_ids)
        self.assertContains(previous_response, "Previous Debt")
        self.assertNotContains(previous_response, "Current Debt")
        self.assertNotContains(previous_response, reverse("debt_payment_delete", args=[previous_month_payment.pk]))
        self.assertNotContains(previous_response, reverse("debt_payment_create"))

        default_response = self.client.get(reverse("debt_payment_list"))
        self.assertEqual(default_response.status_code, 200)
        default_ids = {obj.id for obj in default_response.context["object_list"]}
        self.assertNotIn(previous_month_payment.id, default_ids)
        self.assertNotIn(current_month_payment_on_previous_debt.id, default_ids)
        self.assertIn(current_debt_payment.id, default_ids)


class DebtPaymentCreateAjaxTests(TestCase):
    def setUp(self):
        self.owner = models.User.objects.create_user(username="owner_ajax", password="pass123")
        self.branch_1 = models.Branch.objects.create(name="Branch 1", owner=self.owner)
        self.branch_2 = models.Branch.objects.create(name="Branch 2", owner=self.owner)
        models.BranchUser.objects.create(
            user=self.owner,
            branch=self.branch_1,
            role=models.BranchUser.ROLE_OWNER,
        )
        models.BranchUser.objects.create(
            user=self.owner,
            branch=self.branch_2,
            role=models.BranchUser.ROLE_OWNER,
        )
        self.client.force_login(self.owner)

    def test_payment_create_template_keeps_post_and_has_no_auto_submit(self):
        response = self.client.get(reverse("debt_payment_create"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '<form method="post"', html=False)
        self.assertContains(response, "data-debt-options-url")
        self.assertNotContains(response, "this.form.method='get'; this.form.submit()")

    def test_debt_options_api_returns_only_open_debts_for_selected_branch(self):
        open_debt = models.Debt.objects.create(
            branch=self.branch_1,
            created_by=self.owner,
            f_name="Open Debt",
            amount=Decimal("100"),
            remaining_amount=Decimal("40"),
            direction="WE_GAVE",
        )
        models.Debt.objects.create(
            branch=self.branch_1,
            created_by=self.owner,
            f_name="Closed Debt",
            amount=Decimal("120"),
            remaining_amount=Decimal("0"),
            direction="WE_TOOK",
        )
        models.Debt.objects.create(
            branch=self.branch_2,
            created_by=self.owner,
            f_name="Other Branch Debt",
            amount=Decimal("150"),
            remaining_amount=Decimal("60"),
            direction="WE_GAVE",
        )

        response = self.client.get(
            reverse("debt_payment_debt_options"),
            {"branch": self.branch_1.id},
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(
            payload,
            {
                "debts": [
                    {
                        "id": open_debt.id,
                        "label": "Open Debt — 40.00",
                    }
                ]
            },
        )
