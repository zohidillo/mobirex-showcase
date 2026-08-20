from decimal import Decimal

from django.db import transaction
from django.test import TestCase
from django.utils import timezone

from src.core import models
from src.services.accessory import AccessoryCreateService, AccessorySellService
from src.services.debt import DebtCreateService, DebtPaymentCreateService
from src.services.expense import ExpenseCreateService
from src.services.extra_profit import ExtraProfitCreateService
from src.services.phone import PhoneCreateService, PhoneSellService


class MonthlyBusinessSimulationTest(TestCase):
    def test_monthly_business_flow(self):
        with transaction.atomic():
            owner = models.User.objects.create_user(username="owner", password="pass123")
            phone_seller_1 = models.User.objects.create_user(
                username="phone_seller_1",
                password="pass123",
            )
            phone_seller_2 = models.User.objects.create_user(
                username="phone_seller_2",
                password="pass123",
            )
            accessory_seller = models.User.objects.create_user(
                username="accessory_seller",
                password="pass123",
            )

            branch = models.Branch.objects.create(name="Main Branch", owner=owner)

            models.BranchUser.objects.create(
                user=owner,
                branch=branch,
                role=models.BranchUser.ROLE_OWNER,
            )
            models.BranchUser.objects.create(
                user=phone_seller_1,
                branch=branch,
                role=models.BranchUser.ROLE_PHONE_SELLER,
            )
            models.BranchUser.objects.create(
                user=phone_seller_2,
                branch=branch,
                role=models.BranchUser.ROLE_PHONE_SELLER,
            )
            models.BranchUser.objects.create(
                user=accessory_seller,
                branch=branch,
                role=models.BranchUser.ROLE_ACCESSORY_SELLER,
            )

            month_start = timezone.now().date().replace(day=1)
            capital_amount = Decimal("10000")
            existing_capital = (
                models.PhoneCapital.objects.select_for_update()
                .filter(branch=branch, month=month_start, is_deleted=False)
                .first()
            )
            if existing_capital:
                existing_capital.invested_amount += capital_amount
                existing_capital.current_balance += capital_amount
                existing_capital.save()
            else:
                models.PhoneCapital.objects.create(
                    branch=branch,
                    month=month_start,
                    invested_amount=capital_amount,
                    current_balance=capital_amount,
                )

            phone_category = models.PhoneCategory.objects.create(name="Smartphones")
            phones = []
            for idx in range(10):
                phone = PhoneCreateService.create_phone(
                    {
                        "name": f"Phone {idx + 1}",
                        "category": phone_category,
                        "branch": branch,
                        "imei": f"IMEI-{idx + 1:04d}",
                        "storage": "128",
                        "color": "Black",
                        "from_by": "Supplier",
                        "cost_price": Decimal("500"),
                    },
                    added_by=phone_seller_1,
                )
                phones.append(phone)

            for phone in phones[:7]:
                PhoneSellService.sell_phone(
                    phone=phone,
                    sell_price=Decimal("1000"),
                    sold_by=phone_seller_2,
                )

            accessory_category = models.AccessoryCategory.objects.create(name="Chargers")
            accessory = AccessoryCreateService.create_accessory(
                {
                    "name": "Fast Charger",
                    "category": accessory_category,
                    "branch": branch,
                    "unit_cost": Decimal("200"),
                    "quantity": 10,
                },
                added_by=accessory_seller,
            )
            AccessorySellService.sell_accessory(
                accessory=accessory,
                quantity=10,
                total_price=Decimal("2500"),
                sold_by=accessory_seller,
            )

            ExpenseCreateService.create_expense(
                {
                    "branch": branch,
                    "type": "SHOP_EXPENSE",
                    "amount": Decimal("500"),
                    "note": "Shop expense",
                },
                created_by=phone_seller_1,
            )
            ExpenseCreateService.create_expense(
                {
                    "branch": branch,
                    "type": "EMPLOYEE_EXPENSE",
                    "amount": Decimal("300"),
                    "note": "Employee expense",
                },
                created_by=accessory_seller,
            )

            debt_we_gave = DebtCreateService.create_debt(
                branch=branch,
                amount=Decimal("1000"),
                direction="WE_GAVE",
                created_by=owner,
                note="Loaned out",
            )
            debt_we_took = DebtCreateService.create_debt(
                branch=branch,
                amount=Decimal("1500"),
                direction="WE_TOOK",
                created_by=owner,
                note="Borrowed",
            )

            DebtPaymentCreateService.create_payment(
                debt=debt_we_took,
                amount=Decimal("500"),
                paid_by=owner,
                note="Paid back",
            )
            DebtPaymentCreateService.create_payment(
                debt=debt_we_gave,
                amount=Decimal("800"),
                paid_by=owner,
                note="Returned",
            )

            ExtraProfitCreateService.create_extra_profit(
                {
                    "branch": branch,
                    "amount": Decimal("300"),
                    "note": "Extra profit",
                },
                created_by=phone_seller_1,
            )

        sold_phones = (
            models.Phone.objects.select_related("branch", "category")
            .filter(branch=branch, is_sold=True)
        )
        phone_profit = sum(
            ((phone.sell_price or Decimal("0")) - (phone.cost_price or Decimal("0")))
            for phone in sold_phones
        )

        accessory_sales = models.AccessorySale.objects.select_related(
            "accessory",
            "branch",
        ).filter(branch=branch)
        accessory_profit = sum(
            (sale.profit or Decimal("0")) for sale in accessory_sales
        )

        extra_profit_total = sum(
            (profit.amount or Decimal("0"))
            for profit in models.ExtraProfit.objects.select_related(
                "branch",
                "created_by",
            ).filter(branch=branch)
        )
        expenses_total = sum(
            (expense.amount or Decimal("0"))
            for expense in models.Expense.objects.select_related(
                "branch",
                "created_by",
            ).filter(branch=branch)
        )

        net_profit = phone_profit + accessory_profit + extra_profit_total - expenses_total

        remaining_phones = models.Phone.objects.filter(branch=branch, is_sold=False).count()
        accessory_stock = sum(
            accessory.stock
            for accessory in models.Accessory.objects.select_related(
                "branch",
                "category",
            ).filter(branch=branch)
        )
        stock_count = remaining_phones + accessory_stock

        capital = models.PhoneCapital.objects.select_related("branch").get(
            branch=branch,
            month=month_start,
        )
        current_balance = capital.current_balance

        remaining_debt = sum(
            (debt.remaining_amount or Decimal("0"))
            for debt in models.Debt.objects.select_related(
                "branch",
                "created_by",
            ).filter(branch=branch)
        )

        self.assertEqual(phone_profit, Decimal("3500"))
        self.assertEqual(accessory_profit, Decimal("500"))
        self.assertEqual(net_profit, Decimal("3500"))
        self.assertEqual(stock_count, 3)
        self.assertEqual(remaining_debt, Decimal("1200"))
        self.assertEqual(current_balance, Decimal("12600"))
        self.assertTrue(current_balance >= Decimal("-10000"))

        print("\n===== MONTHLY SIMULATION RESULT =====")
        print("Net Profit:", net_profit)
        print("Current Balance:", current_balance)
        print("Remaining Stock:", stock_count)
        print("Remaining Debt:", remaining_debt)
