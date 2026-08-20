from datetime import datetime, timedelta
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from src.core import models
from src.services.extra_profit import ExtraProfitCreateService


class ExtraProfitWebTests(TestCase):
    def setUp(self):
        self.owner = models.User.objects.create_user(username="owner_extra_web", password="pass123")
        self.phone_seller = models.User.objects.create_user(
            username="phone_seller_extra_web",
            password="pass123",
        )
        self.peer_phone_seller = models.User.objects.create_user(
            username="peer_phone_seller_extra_web",
            password="pass123",
        )
        self.accessory_seller = models.User.objects.create_user(
            username="accessory_seller_extra_web",
            password="pass123",
        )
        self.other_owner = models.User.objects.create_user(
            username="other_owner_extra_web",
            password="pass123",
        )
        self.other_branch_phone_seller = models.User.objects.create_user(
            username="other_branch_phone_extra_web",
            password="pass123",
        )

        self.branch = models.Branch.objects.create(name="Main Extra Branch", owner=self.owner)
        self.second_owned_branch = models.Branch.objects.create(
            name="Second Owned Extra Branch",
            owner=self.owner,
        )
        self.foreign_branch = models.Branch.objects.create(name="Foreign Extra Branch", owner=self.other_owner)

        models.BranchUser.objects.create(
            user=self.owner,
            branch=self.branch,
            role=models.BranchUser.ROLE_OWNER,
        )
        models.BranchUser.objects.create(
            user=self.owner,
            branch=self.second_owned_branch,
            role=models.BranchUser.ROLE_OWNER,
        )
        models.BranchUser.objects.create(
            user=self.other_owner,
            branch=self.foreign_branch,
            role=models.BranchUser.ROLE_OWNER,
        )
        models.BranchUser.objects.create(
            user=self.phone_seller,
            branch=self.branch,
            role=models.BranchUser.ROLE_PHONE_SELLER,
        )
        models.BranchUser.objects.create(
            user=self.peer_phone_seller,
            branch=self.branch,
            role=models.BranchUser.ROLE_PHONE_SELLER,
        )
        models.BranchUser.objects.create(
            user=self.accessory_seller,
            branch=self.branch,
            role=models.BranchUser.ROLE_ACCESSORY_SELLER,
        )
        models.BranchUser.objects.create(
            user=self.other_branch_phone_seller,
            branch=self.foreign_branch,
            role=models.BranchUser.ROLE_PHONE_SELLER,
        )

        self.month_start = timezone.localdate().replace(day=1)
        self.phone_capital = models.PhoneCapital.objects.create(
            branch=self.branch,
            month=self.month_start,
            invested_amount=Decimal("100.00"),
            current_balance=Decimal("100.00"),
        )
        self.accessory_capital = models.AccessoryCapital.objects.create(
            branch=self.branch,
            month=self.month_start,
            invested_amount=Decimal("200.00"),
            current_balance=Decimal("200.00"),
        )
        self.second_branch_phone_capital = models.PhoneCapital.objects.create(
            branch=self.second_owned_branch,
            month=self.month_start,
            invested_amount=Decimal("150.00"),
            current_balance=Decimal("150.00"),
        )
        self.foreign_branch_phone_capital = models.PhoneCapital.objects.create(
            branch=self.foreign_branch,
            month=self.month_start,
            invested_amount=Decimal("300.00"),
            current_balance=Decimal("300.00"),
        )

    def _set_added_at(self, instance, value):
        instance.__class__.all_objects.filter(pk=instance.pk).update(
            added_at=value,
            updated_at=value,
        )
        instance.refresh_from_db()

    def _current_dt(self):
        today = timezone.localdate()
        return timezone.make_aware(datetime(today.year, today.month, 20, 10, 0, 0))

    def _previous_dt(self):
        today = timezone.localdate().replace(day=1)
        previous_month = today - timedelta(days=1)
        return timezone.make_aware(datetime(previous_month.year, previous_month.month, 15, 10, 0, 0))

    def test_web_owner_can_list_and_delete_but_cannot_create(self):
        current_item = ExtraProfitCreateService.create_extra_profit(
            {
                "branch": self.branch,
                "amount": Decimal("20.00"),
                "note": "Owner sees and can delete",
            },
            created_by=self.phone_seller,
        )

        self.client.force_login(self.owner)
        response = self.client.get(reverse("extra_profit_list"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Owner sees and can delete")
        self.assertContains(response, 'name="branch"', html=False)
        self.assertNotContains(response, reverse("extra_profit_create"))

        create_response = self.client.get(reverse("extra_profit_create"))
        delete_response = self.client.post(reverse("extra_profit_delete", args=[current_item.pk]))

        self.assertEqual(create_response.status_code, 302)
        self.assertEqual(delete_response.status_code, 302)
        current_item.refresh_from_db()
        self.assertTrue(current_item.is_deleted)

        phone_capital = models.PhoneCapital.objects.get(branch=self.branch, month=self.month_start)
        self.assertEqual(phone_capital.current_balance, Decimal("100.00"))

    def test_web_default_current_month_year_month_and_branch_filters_work(self):
        current_main = ExtraProfitCreateService.create_extra_profit(
            {
                "branch": self.branch,
                "amount": Decimal("10.00"),
                "note": "Current owned main",
            },
            created_by=self.phone_seller,
        )
        previous_main = ExtraProfitCreateService.create_extra_profit(
            {
                "branch": self.branch,
                "amount": Decimal("11.00"),
                "note": "Previous owned main",
            },
            created_by=self.phone_seller,
        )
        current_second_owned = models.ExtraProfit.objects.create(
            branch=self.second_owned_branch,
            created_by=self.phone_seller,
            amount=Decimal("12.00"),
            note="Current owned second",
        )
        foreign_current = models.ExtraProfit.objects.create(
            branch=self.foreign_branch,
            created_by=self.other_branch_phone_seller,
            amount=Decimal("13.00"),
            note="Foreign current",
        )

        self._set_added_at(current_main, self._current_dt())
        self._set_added_at(previous_main, self._previous_dt())
        self._set_added_at(current_second_owned, self._current_dt())
        self._set_added_at(foreign_current, self._current_dt())

        previous_dt = self._previous_dt()

        self.client.force_login(self.owner)

        default_response = self.client.get(reverse("extra_profit_list"))
        self.assertContains(default_response, "Current owned main")
        self.assertContains(default_response, "Current owned second")
        self.assertNotContains(default_response, "Previous owned main")
        self.assertNotContains(default_response, "Foreign current")

        branch_response = self.client.get(
            reverse("extra_profit_list"),
            {"branch": self.second_owned_branch.id},
        )
        self.assertContains(branch_response, "Current owned second")
        self.assertNotContains(branch_response, "Current owned main")

        previous_response = self.client.get(
            reverse("extra_profit_list"),
            {"year": previous_dt.year, "month": previous_dt.month},
        )
        self.assertContains(previous_response, "Previous owned main")
        self.assertNotContains(previous_response, "Current owned main")

    def test_web_phone_seller_scope_and_delete_rules(self):
        peer_current = ExtraProfitCreateService.create_extra_profit(
            {
                "branch": self.branch,
                "amount": Decimal("25.00"),
                "note": "Peer phone current",
            },
            created_by=self.peer_phone_seller,
        )
        # Accessory seller cannot create via service; use direct DB for testing visibility
        accessory_current = models.ExtraProfit.objects.create(
            branch=self.branch,
            created_by=self.accessory_seller,
            amount=Decimal("30.00"),
            note="Accessory current",
        )
        other_branch_current = models.ExtraProfit.objects.create(
            branch=self.foreign_branch,
            created_by=self.other_branch_phone_seller,
            amount=Decimal("40.00"),
            note="Foreign phone current",
        )
        past_phone = models.ExtraProfit.objects.create(
            branch=self.branch,
            created_by=self.peer_phone_seller,
            amount=Decimal("15.00"),
            note="Peer phone past",
        )
        self._set_added_at(peer_current, self._current_dt())
        self._set_added_at(accessory_current, self._current_dt())
        self._set_added_at(other_branch_current, self._current_dt())
        self._set_added_at(past_phone, self._previous_dt())

        # Only peer_current contributed to phone_capital (+25)
        self.phone_capital.refresh_from_db()
        self.assertEqual(self.phone_capital.current_balance, Decimal("125.00"))

        self.client.force_login(self.phone_seller)

        default_response = self.client.get(reverse("extra_profit_list"))
        # Peer's item is visible (same branch, phone domain)
        self.assertContains(default_response, "Peer phone current")
        # Accessory seller's item is NOT visible to phone seller
        self.assertNotContains(default_response, "Accessory current")
        self.assertNotContains(default_response, "Foreign phone current")
        self.assertNotContains(default_response, "Peer phone past")

        previous_dt = self._previous_dt()
        past_response = self.client.get(
            reverse("extra_profit_list"),
            {"year": previous_dt.year, "month": previous_dt.month},
        )
        self.assertContains(past_response, "Peer phone past")
        self.assertNotContains(past_response, reverse("extra_profit_delete", args=[past_phone.pk]))

        # Phone seller cannot delete peer's item (not own)
        delete_peer = self.client.post(reverse("extra_profit_delete", args=[peer_current.pk]))
        self.assertEqual(delete_peer.status_code, 302)
        peer_current.refresh_from_db()
        self.assertFalse(peer_current.is_deleted)
        self.phone_capital.refresh_from_db()
        self.assertEqual(self.phone_capital.current_balance, Decimal("125.00"))

        # Phone seller can delete own current-month item
        own_current = ExtraProfitCreateService.create_extra_profit(
            {"branch": self.branch, "amount": Decimal("10.00"), "note": "Own phone current"},
            created_by=self.phone_seller,
        )
        self.phone_capital.refresh_from_db()
        self.assertEqual(self.phone_capital.current_balance, Decimal("135.00"))

        delete_own = self.client.post(reverse("extra_profit_delete", args=[own_current.pk]))
        self.assertEqual(delete_own.status_code, 302)
        own_current.refresh_from_db()
        self.assertTrue(own_current.is_deleted)

        self.phone_capital.refresh_from_db()
        self.accessory_capital.refresh_from_db()
        self.foreign_branch_phone_capital.refresh_from_db()
        self.assertEqual(self.phone_capital.current_balance, Decimal("125.00"))
        self.assertEqual(self.accessory_capital.current_balance, Decimal("200.00"))
        self.assertEqual(self.foreign_branch_phone_capital.current_balance, Decimal("300.00"))

        # Past-month and non-visible items cannot be deleted
        delete_past = self.client.post(reverse("extra_profit_delete", args=[past_phone.pk]))
        delete_accessory = self.client.post(reverse("extra_profit_delete", args=[accessory_current.pk]))
        delete_foreign = self.client.post(reverse("extra_profit_delete", args=[other_branch_current.pk]))
        self.assertEqual(delete_past.status_code, 302)
        self.assertEqual(delete_accessory.status_code, 404)
        self.assertEqual(delete_foreign.status_code, 404)

        past_phone.refresh_from_db()
        accessory_current.refresh_from_db()
        other_branch_current.refresh_from_db()
        self.assertFalse(past_phone.is_deleted)
        self.assertFalse(accessory_current.is_deleted)
        self.assertFalse(other_branch_current.is_deleted)

    def test_web_accessory_seller_cannot_create_extra_profit(self):
        """Accessory seller is now blocked from creating or viewing extra profit."""
        self.client.force_login(self.accessory_seller)

        # Access to list is blocked
        list_response = self.client.get(reverse("extra_profit_list"))
        self.assertEqual(list_response.status_code, 302)

        # Create is blocked
        create_response = self.client.post(
            reverse("extra_profit_create"),
            {"amount": "9.00", "note": "Accessory web extra"},
        )
        self.assertEqual(create_response.status_code, 302)

        self.assertFalse(
            models.ExtraProfit.objects.filter(note="Accessory web extra", is_deleted=False).exists()
        )

        self.accessory_capital.refresh_from_db()
        self.phone_capital.refresh_from_db()
        self.assertEqual(self.accessory_capital.current_balance, Decimal("200.00"))
        self.assertEqual(self.phone_capital.current_balance, Decimal("100.00"))
