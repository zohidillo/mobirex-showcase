from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from src.core import models
from src.services.accessory import AccessoryDeleteService, AccessorySellService
from src.services.accessory.returns import AccessoryReturnService
from src.services.expense import ExpenseCreateService
from src.services.salary import SalaryCreateService


class CapitalIsolationTest(TestCase):
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
            user=self.phone_seller,
            branch=self.branch_a,
            role=models.BranchUser.ROLE_PHONE_SELLER,
        )
        models.BranchUser.objects.create(
            user=self.accessory_seller,
            branch=self.branch_a,
            role=models.BranchUser.ROLE_ACCESSORY_SELLER,
        )

        month_start = timezone.now().date().replace(day=1)
        self.phone_capital_a = models.PhoneCapital.objects.create(
            branch=self.branch_a,
            month=month_start,
            invested_amount=Decimal("0"),
            current_balance=Decimal("1000"),
        )
        self.accessory_capital_a = models.AccessoryCapital.objects.create(
            branch=self.branch_a,
            month=month_start,
            invested_amount=Decimal("0"),
            current_balance=Decimal("1000"),
        )
        self.phone_capital_b = models.PhoneCapital.objects.create(
            branch=self.branch_b,
            month=month_start,
            invested_amount=Decimal("0"),
            current_balance=Decimal("1000"),
        )
        self.accessory_capital_b = models.AccessoryCapital.objects.create(
            branch=self.branch_b,
            month=month_start,
            invested_amount=Decimal("0"),
            current_balance=Decimal("1000"),
        )

    def test_accessory_seller_salary_deducts_accessory_capital_only(self):
        SalaryCreateService.create_salary(
            {
                "branch": self.branch_a,
                "employee": self.accessory_seller,
                "amount": Decimal("200"),
                "note": "Accessory seller salary",
            },
            created_by=self.accessory_seller,
        )

        self.phone_capital_a.refresh_from_db()
        self.accessory_capital_a.refresh_from_db()

        self.assertEqual(self.phone_capital_a.current_balance, Decimal("1000"))
        self.assertEqual(self.accessory_capital_a.current_balance, Decimal("800"))

    def test_phone_seller_expense_deducts_phone_capital_only(self):
        ExpenseCreateService.create_expense(
            {
                "branch": self.branch_a,
                "type": "SHOP_EXPENSE",
                "amount": Decimal("150"),
                "note": "Phone seller expense",
            },
            created_by=self.phone_seller,
        )

        self.phone_capital_a.refresh_from_db()
        self.accessory_capital_a.refresh_from_db()

        self.assertEqual(self.phone_capital_a.current_balance, Decimal("850"))
        self.assertEqual(self.accessory_capital_a.current_balance, Decimal("1000"))

    def test_cross_branch_modification_blocked(self):
        with self.assertRaises(ValidationError):
            ExpenseCreateService.create_expense(
                {
                    "branch": self.branch_b,
                    "type": "SHOP_EXPENSE",
                    "amount": Decimal("50"),
                    "note": "Unauthorized",
                },
                created_by=self.phone_seller,
            )

        self.phone_capital_a.refresh_from_db()
        self.accessory_capital_a.refresh_from_db()
        self.phone_capital_b.refresh_from_db()
        self.accessory_capital_b.refresh_from_db()

        self.assertEqual(self.phone_capital_a.current_balance, Decimal("1000"))
        self.assertEqual(self.accessory_capital_a.current_balance, Decimal("1000"))
        self.assertEqual(self.phone_capital_b.current_balance, Decimal("1000"))
        self.assertEqual(self.accessory_capital_b.current_balance, Decimal("1000"))


class AccessoryCapitalIsolationTest(TestCase):
    """Capital isolation tests specific to accessory create/sell/return/delete flows."""

    def setUp(self):
        self.owner = models.User.objects.create_user(username="acc_owner", password="pass123")
        self.accessory_seller = models.User.objects.create_user(
            username="acc_seller",
            password="pass123",
        )
        self.phone_seller = models.User.objects.create_user(
            username="acc_phone_seller",
            password="pass123",
        )

        self.branch_a = models.Branch.objects.create(name="Acc Branch A", owner=self.owner)
        self.branch_b = models.Branch.objects.create(name="Acc Branch B", owner=self.owner)

        models.BranchUser.objects.create(
            user=self.owner,
            branch=self.branch_a,
            role=models.BranchUser.ROLE_OWNER,
        )
        models.BranchUser.objects.create(
            user=self.accessory_seller,
            branch=self.branch_a,
            role=models.BranchUser.ROLE_ACCESSORY_SELLER,
        )
        models.BranchUser.objects.create(
            user=self.phone_seller,
            branch=self.branch_a,
            role=models.BranchUser.ROLE_PHONE_SELLER,
        )

        self.category = models.AccessoryCategory.objects.create(name="Acc Test Category")
        month_start = timezone.now().date().replace(day=1)

        self.acc_capital_a = models.AccessoryCapital.objects.create(
            branch=self.branch_a,
            month=month_start,
            invested_amount=Decimal("100"),
            current_balance=Decimal("100"),
        )
        self.phone_capital_a = models.PhoneCapital.objects.create(
            branch=self.branch_a,
            month=month_start,
            invested_amount=Decimal("0"),
            current_balance=Decimal("1000"),
        )
        self.acc_capital_b = models.AccessoryCapital.objects.create(
            branch=self.branch_b,
            month=month_start,
            invested_amount=Decimal("0"),
            current_balance=Decimal("500"),
        )

        self.accessory = models.Accessory.objects.create(
            name="Test Accessory",
            category=self.category,
            branch=self.branch_a,
            unit_cost=Decimal("10.00"),
            stock=10,
            added_by=self.owner,
        )

    def test_accessory_sell_increases_accessory_capital_not_phone_capital(self):
        AccessorySellService.sell_accessory(
            self.accessory, quantity=2, total_price=Decimal("30.00"), sold_by=self.accessory_seller
        )

        self.acc_capital_a.refresh_from_db()
        self.phone_capital_a.refresh_from_db()

        self.assertEqual(self.acc_capital_a.current_balance, Decimal("130"))   # +30
        self.assertEqual(self.phone_capital_a.current_balance, Decimal("1000"))  # untouched

    def test_accessory_return_restores_stock_and_subtracts_accessory_capital(self):
        sale = AccessorySellService.sell_accessory(
            self.accessory, quantity=2, total_price=Decimal("30.00"), sold_by=self.accessory_seller
        )
        self.acc_capital_a.refresh_from_db()
        balance_after_sell = self.acc_capital_a.current_balance  # 100 + 30 = 130

        AccessoryReturnService.return_sale(sale, returned_by=self.accessory_seller)

        self.acc_capital_a.refresh_from_db()
        self.accessory.refresh_from_db()

        self.assertEqual(self.accessory.stock, 10)                              # restored
        self.assertEqual(self.acc_capital_a.current_balance, balance_after_sell - Decimal("30"))  # -30

    def test_accessory_return_does_not_touch_phone_capital(self):
        sale = AccessorySellService.sell_accessory(
            self.accessory, quantity=1, total_price=Decimal("15.00"), sold_by=self.accessory_seller
        )
        AccessoryReturnService.return_sale(sale, returned_by=self.accessory_seller)

        self.phone_capital_a.refresh_from_db()
        self.assertEqual(self.phone_capital_a.current_balance, Decimal("1000"))

    def test_accessory_delete_rolls_back_invested_amount_only(self):
        # stock=10, unit_cost=10 → remaining_value = 100
        AccessoryDeleteService.delete_accessory(self.accessory, deleted_by=self.accessory_seller)

        self.acc_capital_a.refresh_from_db()
        self.assertEqual(self.acc_capital_a.invested_amount, Decimal("0"))      # 100 - 100
        self.assertEqual(self.acc_capital_a.current_balance, Decimal("100"))    # unchanged

    def test_accessory_delete_does_not_touch_phone_capital(self):
        AccessoryDeleteService.delete_accessory(self.accessory, deleted_by=self.accessory_seller)

        self.phone_capital_a.refresh_from_db()
        self.assertEqual(self.phone_capital_a.current_balance, Decimal("1000"))

    def test_accessory_sell_does_not_affect_other_branch_capital(self):
        AccessorySellService.sell_accessory(
            self.accessory, quantity=1, total_price=Decimal("20.00"), sold_by=self.accessory_seller
        )

        self.acc_capital_b.refresh_from_db()
        self.assertEqual(self.acc_capital_b.current_balance, Decimal("500"))  # untouched

    def test_accessory_return_blocked_for_soft_deleted_accessory(self):
        sale = AccessorySellService.sell_accessory(
            self.accessory, quantity=1, total_price=Decimal("15.00"), sold_by=self.accessory_seller
        )
        # Force-delete accessory without going through service
        models.Accessory.all_objects.filter(pk=self.accessory.pk).update(is_deleted=True)
        sale.refresh_from_db()
        # Reload the related accessory so the in-memory object reflects the deletion
        sale = models.AccessorySale.objects.select_related("accessory").get(pk=sale.pk)

        with self.assertRaises(ValidationError):
            AccessoryReturnService.return_sale(sale, returned_by=self.accessory_seller)

        # Stock and capital must remain unchanged
        accessory = models.Accessory.all_objects.get(pk=self.accessory.pk)
        self.acc_capital_a.refresh_from_db()
        self.assertEqual(accessory.stock, 9)  # still reduced from sell, not restored
        self.assertFalse(models.AccessorySale.all_objects.get(pk=sale.pk).is_deleted)

    def test_accessory_delete_blocked_when_active_sale_exists(self):
        AccessorySellService.sell_accessory(
            self.accessory, quantity=3, total_price=Decimal("45.00"), sold_by=self.accessory_seller
        )

        with self.assertRaises(ValueError):
            AccessoryDeleteService.delete_accessory(
                self.accessory, deleted_by=self.accessory_seller
            )

        self.accessory.refresh_from_db()
        self.assertFalse(self.accessory.is_deleted)
