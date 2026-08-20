from datetime import datetime, timedelta
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from src.core import models
from src.services.expense import ExpenseCreateService, ExpenseDeleteService


class ExpenseCapitalDeductionTest(TestCase):
    def test_accessory_seller_expense_deducts_accessory_capital_only(self):
        owner = models.User.objects.create_user(username="owner", password="pass123")
        phone_seller = models.User.objects.create_user(
            username="phone_seller",
            password="pass123",
        )
        accessory_seller = models.User.objects.create_user(
            username="accessory_seller",
            password="pass123",
        )

        branch = models.Branch.objects.create(name="Main Branch", owner=owner)
        models.BranchUser.objects.create(
            user=phone_seller,
            branch=branch,
            role=models.BranchUser.ROLE_PHONE_SELLER,
        )
        models.BranchUser.objects.create(
            user=accessory_seller,
            branch=branch,
            role=models.BranchUser.ROLE_ACCESSORY_SELLER,
        )

        month_start = timezone.now().date().replace(day=1)
        phone_capital = models.PhoneCapital.objects.create(
            branch=branch,
            month=month_start,
            invested_amount=Decimal("0"),
            current_balance=Decimal("1000"),
        )
        accessory_capital = models.AccessoryCapital.objects.create(
            branch=branch,
            month=month_start,
            invested_amount=Decimal("0"),
            current_balance=Decimal("1000"),
        )

        ExpenseCreateService.create_expense(
            {
                "branch": branch,
                "type": "EMPLOYEE_EXPENSE",
                "amount": Decimal("200"),
                "note": "Accessory seller expense",
            },
            created_by=accessory_seller,
        )

        phone_capital.refresh_from_db()
        accessory_capital.refresh_from_db()

        self.assertEqual(phone_capital.current_balance, Decimal("1000"))
        self.assertEqual(accessory_capital.current_balance, Decimal("800"))

    def test_owner_cannot_create_expense_via_service(self):
        owner = models.User.objects.create_user(username="owner_only", password="pass123")
        branch = models.Branch.objects.create(name="Main Branch", owner=owner)
        models.BranchUser.objects.create(
            user=owner,
            branch=branch,
            role=models.BranchUser.ROLE_OWNER,
        )

        with self.assertRaises(ValidationError):
            ExpenseCreateService.create_expense(
                {
                    "branch": branch,
                    "type": "SHOP_EXPENSE",
                    "amount": Decimal("200"),
                    "note": "Owner expense",
                },
                created_by=owner,
            )

    def test_past_month_expense_delete_is_blocked(self):
        owner = models.User.objects.create_user(username="owner_month", password="pass123")
        phone_seller = models.User.objects.create_user(
            username="phone_seller_month",
            password="pass123",
        )

        branch = models.Branch.objects.create(name="Main Branch", owner=owner)
        models.BranchUser.objects.create(
            user=phone_seller,
            branch=branch,
            role=models.BranchUser.ROLE_PHONE_SELLER,
        )

        current_month_start = timezone.localdate().replace(day=1)
        previous_month_date = current_month_start - timedelta(days=1)
        previous_month_start = previous_month_date.replace(day=1)

        previous_capital = models.PhoneCapital.objects.create(
            branch=branch,
            month=previous_month_start,
            invested_amount=Decimal("0"),
            current_balance=Decimal("850"),
        )
        current_capital = models.PhoneCapital.objects.create(
            branch=branch,
            month=current_month_start,
            invested_amount=Decimal("0"),
            current_balance=Decimal("700"),
        )

        expense = models.Expense.objects.create(
            branch=branch,
            created_by=phone_seller,
            type="SHOP_EXPENSE",
            amount=Decimal("150"),
            capital_type=models.Expense.CAPITAL_TYPE_PHONE,
            note="Historical expense",
        )
        models.Expense.all_objects.filter(pk=expense.pk).update(
            added_at=timezone.make_aware(
                datetime(
                    previous_month_start.year,
                    previous_month_start.month,
                    10,
                    10,
                    0,
                    0,
                )
            )
        )
        expense.refresh_from_db()

        with self.assertRaises(ValidationError):
            ExpenseDeleteService.delete_expense(expense, deleted_by=phone_seller)

        previous_capital.refresh_from_db()
        current_capital.refresh_from_db()
        expense.refresh_from_db()

        self.assertEqual(previous_capital.current_balance, Decimal("850"))
        self.assertEqual(current_capital.current_balance, Decimal("700"))
        self.assertFalse(expense.is_deleted)

    def test_owner_can_delete_current_month_expense_via_service(self):
        owner = models.User.objects.create_user(username="owner_delete", password="pass123")
        phone_seller = models.User.objects.create_user(
            username="phone_seller_delete",
            password="pass123",
        )

        branch = models.Branch.objects.create(name="Main Branch", owner=owner)
        models.BranchUser.objects.create(
            user=owner,
            branch=branch,
            role=models.BranchUser.ROLE_OWNER,
        )
        models.BranchUser.objects.create(
            user=phone_seller,
            branch=branch,
            role=models.BranchUser.ROLE_PHONE_SELLER,
        )

        month_start = timezone.localdate().replace(day=1)
        models.PhoneCapital.objects.create(
            branch=branch,
            month=month_start,
            invested_amount=Decimal("0"),
            current_balance=Decimal("500"),
        )

        expense = models.Expense.objects.create(
            branch=branch,
            created_by=phone_seller,
            type="SHOP_EXPENSE",
            amount=Decimal("50"),
            capital_type=models.Expense.CAPITAL_TYPE_PHONE,
            note="Seller expense",
        )

        ExpenseDeleteService.delete_expense(expense, deleted_by=owner)

        expense.refresh_from_db()
        self.assertTrue(expense.is_deleted)
