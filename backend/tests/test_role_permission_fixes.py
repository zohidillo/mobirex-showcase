from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from src.core import models
from src.services.debt import DebtCreateService, DebtPaymentCreateService


class RolePermissionFixesTest(TestCase):
    def setUp(self):
        self.owner = models.User.objects.create_user(username="owner", password="pass123")
        self.phone_seller = models.User.objects.create_user(
            username="phone_seller",
            password="pass123",
        )
        self.accessory_seller = models.User.objects.create_user(
            username="accessory_seller",
            password="pass123",
        )

        self.branch_a = models.Branch.objects.create(name="Branch A", owner=self.owner)
        self.branch_b = models.Branch.objects.create(name="Branch B", owner=self.owner)

        models.BranchUser.objects.create(
            user=self.owner,
            branch=self.branch_a,
            role=models.BranchUser.ROLE_OWNER,
        )
        models.BranchUser.objects.create(
            user=self.phone_seller,
            branch=self.branch_a,
            role=models.BranchUser.ROLE_PHONE_SELLER,
        )
        models.BranchUser.objects.create(
            user=self.accessory_seller,
            branch=self.branch_a,
            role=models.BranchUser.ROLE_ACCESSORY_SELLER,
        )

        self.phone_category = models.PhoneCategory.objects.create(name="Smartphone")
        self.accessory_category = models.AccessoryCategory.objects.create(name="Case")

        self.month_start = timezone.now().date().replace(day=1)

    def test_seller_cannot_access_other_branch_data(self):
        other_branch_debt = models.Debt.objects.create(
            branch=self.branch_b,
            created_by=self.owner,
            f_name="Other Branch",
            amount=Decimal("100"),
            remaining_amount=Decimal("100"),
            direction="WE_GAVE",
        )

        self.client.force_login(self.phone_seller)
        response = self.client.post(reverse("debt_delete", args=[other_branch_debt.pk]))

        self.assertEqual(response.status_code, 302)
        other_branch_debt.refresh_from_db()
        self.assertFalse(other_branch_debt.is_deleted)

    def test_debt_payment_affects_capital_based_on_debt_origin(self):
        phone_capital = models.PhoneCapital.objects.create(
            branch=self.branch_a,
            month=self.month_start,
            invested_amount=Decimal("0"),
            current_balance=Decimal("1000"),
        )
        accessory_capital = models.AccessoryCapital.objects.create(
            branch=self.branch_a,
            month=self.month_start,
            invested_amount=Decimal("0"),
            current_balance=Decimal("1000"),
        )

        debt = DebtCreateService.create_debt(
            branch=self.branch_a,
            f_name="Phone debt",
            amount=Decimal("200"),
            direction="WE_GAVE",
            created_by=self.phone_seller,
            note="Created by phone seller",
        )
        self.assertEqual(debt.domain, models.Debt.DOMAIN_PHONE)

        DebtPaymentCreateService.create_payment(
            debt=debt,
            amount=Decimal("50"),
            paid_by=self.owner,
            note="Owner payment should still hit phone capital",
        )

        phone_capital.refresh_from_db()
        accessory_capital.refresh_from_db()

        self.assertEqual(phone_capital.current_balance, Decimal("850"))
        self.assertEqual(accessory_capital.current_balance, Decimal("1000"))

    def test_cross_domain_payment_is_blocked_at_service_layer(self):
        models.PhoneCapital.objects.create(
            branch=self.branch_a,
            month=self.month_start,
            invested_amount=Decimal("0"),
            current_balance=Decimal("1000"),
        )
        models.AccessoryCapital.objects.create(
            branch=self.branch_a,
            month=self.month_start,
            invested_amount=Decimal("0"),
            current_balance=Decimal("1000"),
        )

        debt = DebtCreateService.create_debt(
            branch=self.branch_a,
            f_name="Phone debt",
            amount=Decimal("200"),
            direction="WE_GAVE",
            created_by=self.phone_seller,
            note="Created by phone seller",
        )

        with self.assertRaises(ValidationError):
            DebtPaymentCreateService.create_payment(
                debt=debt,
                amount=Decimal("50"),
                paid_by=self.accessory_seller,
                note="Cross-domain payment",
            )

        self.assertFalse(
            models.DebtPayment.objects.filter(
                debt=debt,
                note="Cross-domain payment",
                is_deleted=False,
            ).exists()
        )

    def test_owner_views_only_owner_role_branches(self):
        self.client.force_login(self.owner)

        response = self.client.get(reverse("owner-branches"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Branch A")
        self.assertNotContains(response, "Branch B")

    def test_owner_cannot_open_expense_create_but_can_delete(self):
        month_start = timezone.now().date().replace(day=1)
        models.PhoneCapital.objects.create(
            branch=self.branch_a,
            month=month_start,
            invested_amount=Decimal("0"),
            current_balance=Decimal("500"),
        )
        expense = models.Expense.objects.create(
            branch=self.branch_a,
            created_by=self.phone_seller,
            type="SHOP_EXPENSE",
            amount=Decimal("25"),
            capital_type=models.Expense.CAPITAL_TYPE_PHONE,
            note="Seller expense",
        )

        self.client.force_login(self.owner)

        create_response = self.client.get(reverse("expense_create"))
        delete_response = self.client.post(reverse("expense_delete", args=[expense.pk]))

        self.assertEqual(create_response.status_code, 302)
        self.assertEqual(delete_response.status_code, 302)
        expense.refresh_from_db()
        self.assertTrue(expense.is_deleted)

    def test_owner_cannot_open_debt_create(self):
        self.client.force_login(self.owner)

        response = self.client.get(reverse("debt_create"))

        self.assertEqual(response.status_code, 302)

    def test_same_branch_same_domain_seller_can_pay_peer_debt_but_not_wrong_domain(self):
        peer_phone_seller = models.User.objects.create_user(
            username="peer_phone_seller",
            password="pass123",
        )
        models.BranchUser.objects.create(
            user=peer_phone_seller,
            branch=self.branch_a,
            role=models.BranchUser.ROLE_PHONE_SELLER,
        )
        peer_debt = DebtCreateService.create_debt(
            branch=self.branch_a,
            f_name="Peer debt",
            amount=Decimal("140"),
            direction="WE_GAVE",
            created_by=peer_phone_seller,
            note="Peer debt",
        )
        wrong_domain_debt = models.Debt.objects.create(
            branch=self.branch_a,
            created_by=self.accessory_seller,
            f_name="Accessory debt",
            domain=models.Debt.DOMAIN_ACCESSORY,
            amount=Decimal("80"),
            remaining_amount=Decimal("80"),
            direction="WE_GAVE",
        )

        self.client.force_login(self.phone_seller)

        options_response = self.client.get(reverse("debt_payment_debt_options"))
        self.assertEqual(options_response.status_code, 200)
        option_ids = {item["id"] for item in options_response.json()["debts"]}
        self.assertIn(peer_debt.id, option_ids)
        self.assertNotIn(wrong_domain_debt.id, option_ids)

        allowed_payment = self.client.post(
            reverse("debt_payment_create"),
            {"debt": peer_debt.id, "amount": "10", "note": "Allowed peer payment"},
        )
        self.assertEqual(allowed_payment.status_code, 302)
        self.assertTrue(
            models.DebtPayment.objects.filter(
                debt=peer_debt,
                note="Allowed peer payment",
                is_deleted=False,
            ).exists()
        )

        blocked_payment = self.client.post(
            reverse("debt_payment_create"),
            {"debt": wrong_domain_debt.id, "amount": "10", "note": "Blocked wrong domain"},
        )
        self.assertEqual(blocked_payment.status_code, 200)
        self.assertFalse(
            models.DebtPayment.objects.filter(
                debt=wrong_domain_debt,
                note="Blocked wrong domain",
                is_deleted=False,
            ).exists()
        )

    def test_no_permission_escalation_on_expense_delete(self):
        owner_expense = models.Expense.objects.create(
            branch=self.branch_a,
            created_by=self.owner,
            type="SHOP_EXPENSE",
            amount=Decimal("25"),
            note="Owner expense",
        )

        self.client.force_login(self.phone_seller)
        delete_response = self.client.post(reverse("expense_delete", args=[owner_expense.pk]))
        self.assertEqual(delete_response.status_code, 302)
        owner_expense.refresh_from_db()
        self.assertFalse(owner_expense.is_deleted)

    def test_seller_payment_options_hide_wrong_domain_debts(self):
        mismatched_debt = models.Debt.objects.create(
            branch=self.branch_a,
            created_by=self.accessory_seller,
            f_name="Wrong Domain Debt",
            domain=models.Debt.DOMAIN_PHONE,
            amount=Decimal("100"),
            remaining_amount=Decimal("100"),
            direction="WE_GAVE",
        )

        self.client.force_login(self.accessory_seller)

        options_response = self.client.get(reverse("debt_payment_debt_options"))
        self.assertEqual(options_response.status_code, 200)
        option_ids = {item["id"] for item in options_response.json()["debts"]}
        self.assertNotIn(mismatched_debt.id, option_ids)

    def test_existing_create_sell_and_payment_flows_still_work(self):
        self.client.force_login(self.owner)
        create_response = self.client.post(
            reverse("accessory_create"),
            {
                "branch": self.branch_a.id,
                "name": "Silicone Case",
                "category": self.accessory_category.id,
                "stock": "3",
                "unit_cost": "12.00",
            },
        )
        self.assertEqual(create_response.status_code, 302)
        accessory = models.Accessory.objects.get(name="Silicone Case")
        self.assertEqual(accessory.branch_id, self.branch_a.id)
        self.assertEqual(accessory.stock, 3)

        phone = models.Phone.objects.create(
            name="iPhone 15",
            category=self.phone_category,
            branch=self.branch_a,
            imei="123456789012345",
            storage="128GB",
            color="Black",
            from_by="Supplier",
            cost_price=Decimal("500"),
            added_by=self.owner,
        )

        self.client.force_login(self.phone_seller)
        sell_response = self.client.post(
            reverse("phone_sell", args=[phone.pk]),
            {"sell_price": "650"},
        )
        self.assertEqual(sell_response.status_code, 302)
        phone.refresh_from_db()
        self.assertTrue(phone.is_sold)
        self.assertEqual(phone.sell_price, Decimal("650"))

        debt = DebtCreateService.create_debt(
            branch=self.branch_a,
            f_name="Working debt",
            amount=Decimal("90"),
            direction="WE_GAVE",
            created_by=self.phone_seller,
            note="Still works",
        )
        payment_response = self.client.post(
            reverse("debt_payment_create"),
            {
                "debt": debt.id,
                "amount": "30",
                "note": "Valid payment",
            },
        )
        self.assertEqual(payment_response.status_code, 302)
        debt.refresh_from_db()
        self.assertEqual(debt.remaining_amount, Decimal("60"))
