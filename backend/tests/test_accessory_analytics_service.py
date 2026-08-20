from decimal import Decimal

from django.test import TestCase

from src.core import models
from src.services.accessory import (
    AccessoryAnalyticsService,
    AccessoryCreateService,
    AccessorySellService,
    calculate_inventory_value,
)


class AccessoryAnalyticsServiceTests(TestCase):
    def setUp(self):
        self.owner = models.User.objects.create_user(
            username="analytics_owner",
            password="pass123",
        )
        self.accessory_seller = models.User.objects.create_user(
            username="analytics_accessory_seller",
            password="pass123",
        )
        self.branch = models.Branch.objects.create(
            name="Analytics Branch",
            owner=self.owner,
        )
        models.BranchUser.objects.create(
            user=self.accessory_seller,
            branch=self.branch,
            role=models.BranchUser.ROLE_ACCESSORY_SELLER,
        )
        self.category = models.AccessoryCategory.objects.create(name="Analytics Category")

    def _create_accessory(
        self,
        *,
        name,
        stock,
        unit_cost,
        is_active=True,
    ):
        return models.Accessory.objects.create(
            name=name,
            category=self.category,
            branch=self.branch,
            unit_cost=unit_cost,
            stock=stock,
            added_by=self.owner,
            is_active=is_active,
        )

    def test_calculate_inventory_value_sums_only_active_non_deleted_stock(self):
        self._create_accessory(
            name="Active Charger",
            stock=5,
            unit_cost=Decimal("10.00"),
        )
        self._create_accessory(
            name="Active Cable",
            stock=3,
            unit_cost=Decimal("7.50"),
        )
        self._create_accessory(
            name="Zero Stock",
            stock=0,
            unit_cost=Decimal("100.00"),
        )
        self._create_accessory(
            name="Inactive Item",
            stock=4,
            unit_cost=Decimal("12.00"),
            is_active=False,
        )
        deleted_accessory = self._create_accessory(
            name="Deleted Item",
            stock=2,
            unit_cost=Decimal("99.00"),
        )
        deleted_accessory.delete()

        inventory_value = calculate_inventory_value(self.branch)

        self.assertEqual(inventory_value, Decimal("72.50"))
        self.assertEqual(
            AccessoryAnalyticsService.get_inventory_value(self.branch),
            Decimal("72.50"),
        )

    def test_inventory_value_decreases_after_accessory_sale(self):
        accessory = AccessoryCreateService.create_accessory(
            {
                "name": "Power Bank",
                "category": self.category,
                "branch": self.branch,
                "unit_cost": Decimal("15.00"),
                "quantity": 10,
            },
            added_by=self.accessory_seller,
        )

        self.assertEqual(calculate_inventory_value(self.branch), Decimal("150.00"))

        AccessorySellService.sell_accessory(
            accessory=accessory,
            quantity=4,
            total_price=Decimal("100.00"),
            sold_by=self.accessory_seller,
        )

        accessory.refresh_from_db()
        self.assertEqual(accessory.stock, 6)
        self.assertEqual(calculate_inventory_value(self.branch), Decimal("90.00"))

    def test_analytics_does_not_change_current_balance(self):
        accessory = AccessoryCreateService.create_accessory(
            {
                "name": "Earbuds",
                "category": self.category,
                "branch": self.branch,
                "unit_cost": Decimal("20.00"),
                "quantity": 5,
            },
            added_by=self.accessory_seller,
        )
        AccessorySellService.sell_accessory(
            accessory=accessory,
            quantity=2,
            total_price=Decimal("70.00"),
            sold_by=self.accessory_seller,
        )

        capital = models.AccessoryCapital.objects.get(branch=self.branch)
        self.assertEqual(capital.current_balance, Decimal("70.00"))

        inventory_value = AccessoryAnalyticsService.get_inventory_value(self.branch)
        total_capital = AccessoryAnalyticsService.get_total_capital(self.branch)

        capital.refresh_from_db()
        self.assertEqual(inventory_value, Decimal("60.00"))
        self.assertEqual(total_capital, Decimal("130.00"))
        self.assertEqual(capital.current_balance, Decimal("70.00"))

    def test_existing_accessory_create_and_sell_behavior_remains_unchanged(self):
        accessory = AccessoryCreateService.create_accessory(
            {
                "name": "Adapter",
                "category": self.category,
                "branch": self.branch,
                "unit_cost": Decimal("5.00"),
                "quantity": 8,
            },
            added_by=self.accessory_seller,
        )

        capital = models.AccessoryCapital.objects.get(branch=self.branch)
        self.assertEqual(capital.invested_amount, Decimal("40.00"))
        self.assertEqual(capital.current_balance, Decimal("0.00"))

        AccessorySellService.sell_accessory(
            accessory=accessory,
            quantity=3,
            total_price=Decimal("24.00"),
            sold_by=self.accessory_seller,
        )

        capital.refresh_from_db()
        capital_count_before = models.AccessoryCapital.objects.filter(branch=self.branch).count()
        sale_count_before = models.AccessorySale.objects.filter(branch=self.branch).count()

        total_capital = AccessoryAnalyticsService.get_total_capital(self.branch)

        accessory.refresh_from_db()
        capital.refresh_from_db()
        capital_count_after = models.AccessoryCapital.objects.filter(branch=self.branch).count()
        sale_count_after = models.AccessorySale.objects.filter(branch=self.branch).count()

        self.assertEqual(accessory.stock, 5)
        self.assertEqual(capital.invested_amount, Decimal("40.00"))
        self.assertEqual(capital.current_balance, Decimal("24.00"))
        self.assertEqual(total_capital, Decimal("49.00"))
        self.assertEqual(capital_count_before, 1)
        self.assertEqual(capital_count_after, 1)
        self.assertEqual(sale_count_before, 1)
        self.assertEqual(sale_count_after, 1)
