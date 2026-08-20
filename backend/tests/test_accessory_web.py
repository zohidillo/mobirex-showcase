from decimal import Decimal

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from src.core import models
from src.services.accessory import AccessorySellService


class AccessoryWebDeleteTest(TestCase):
    """Web-view-level tests for accessory delete safety and multi-branch owner support."""

    def setUp(self):
        self.owner = models.User.objects.create_user(username="web_owner", password="pass123")
        self.accessory_seller = models.User.objects.create_user(
            username="web_seller", password="pass123"
        )
        self.phone_seller = models.User.objects.create_user(
            username="web_phone_seller", password="pass123"
        )

        self.branch_a = models.Branch.objects.create(name="Web Branch A", owner=self.owner)
        self.branch_b = models.Branch.objects.create(name="Web Branch B", owner=self.owner)

        models.BranchUser.objects.create(
            user=self.owner,
            branch=self.branch_a,
            role=models.BranchUser.ROLE_OWNER,
        )
        models.BranchUser.objects.create(
            user=self.owner,
            branch=self.branch_b,
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

        self.category = models.AccessoryCategory.objects.create(name="Web Test Category")
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
            invested_amount=Decimal("50"),
            current_balance=Decimal("50"),
        )

        self.accessory_a = models.Accessory.objects.create(
            name="Web Accessory A",
            category=self.category,
            branch=self.branch_a,
            unit_cost=Decimal("10.00"),
            stock=5,
            added_by=self.owner,
        )
        self.accessory_b = models.Accessory.objects.create(
            name="Web Accessory B",
            category=self.category,
            branch=self.branch_b,
            unit_cost=Decimal("10.00"),
            stock=5,
            added_by=self.owner,
        )

    def _delete_url(self, accessory):
        return reverse("accessory_delete", args=[accessory.pk])

    def test_web_delete_blocked_when_active_sale_exists(self):
        AccessorySellService.sell_accessory(
            self.accessory_a,
            quantity=2,
            total_price=Decimal("30.00"),
            sold_by=self.accessory_seller,
        )

        self.client.force_login(self.owner)
        self.client.post(self._delete_url(self.accessory_a))

        self.accessory_a.refresh_from_db()
        self.assertFalse(self.accessory_a.is_deleted)

    def test_web_delete_allowed_after_all_sales_returned(self):
        from src.services.accessory.returns import AccessoryReturnService

        sale = AccessorySellService.sell_accessory(
            self.accessory_a,
            quantity=2,
            total_price=Decimal("30.00"),
            sold_by=self.accessory_seller,
        )
        AccessoryReturnService.return_sale(sale, returned_by=self.accessory_seller)

        self.client.force_login(self.owner)
        self.client.post(self._delete_url(self.accessory_a))

        self.accessory_a.refresh_from_db()
        self.assertTrue(self.accessory_a.is_deleted)

    def test_web_delete_rolls_back_invested_amount_not_current_balance(self):
        # stock=5, unit_cost=10 → remaining_value = 50
        self.client.force_login(self.owner)
        self.client.post(self._delete_url(self.accessory_a))

        self.acc_capital_a.refresh_from_db()
        self.assertEqual(self.acc_capital_a.invested_amount, Decimal("50"))   # 100 - 50
        self.assertEqual(self.acc_capital_a.current_balance, Decimal("100"))  # unchanged

    def test_web_delete_does_not_touch_phone_capital(self):
        self.client.force_login(self.owner)
        self.client.post(self._delete_url(self.accessory_a))

        self.phone_capital_a.refresh_from_db()
        self.assertEqual(self.phone_capital_a.current_balance, Decimal("1000"))

    def test_web_multi_branch_owner_can_delete_from_second_branch(self):
        # owner has ROLE_OWNER in both branch_a and branch_b (set up in setUp)
        self.client.force_login(self.owner)
        self.client.post(self._delete_url(self.accessory_b))

        self.accessory_b.refresh_from_db()
        self.assertTrue(self.accessory_b.is_deleted)

        self.acc_capital_b.refresh_from_db()
        self.assertEqual(self.acc_capital_b.invested_amount, Decimal("0"))  # 50 - 50

    def test_web_phone_seller_cannot_delete_accessory(self):
        self.client.force_login(self.phone_seller)
        self.client.post(self._delete_url(self.accessory_a))

        self.accessory_a.refresh_from_db()
        self.assertFalse(self.accessory_a.is_deleted)
