"""Debt web/API/service parity tests.

Covers create/list/pay/delete permissions, capital isolation,
and web-API policy alignment for all debt business rules.
"""
from decimal import Decimal

import pytest
from django.core.exceptions import PermissionDenied
from django.urls import reverse
from django.utils import timezone

from src.core import models
from src.services.debt import (
    DebtCreateService,
    DebtDeleteService,
    DebtPaymentCreateService,
    DebtPaymentDeleteService,
)

pytestmark = pytest.mark.django_db


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _month_start():
    return timezone.localdate().replace(day=1)


def _make_capital(model_cls, branch, balance=Decimal("1000.00")):
    return model_cls.objects.create(
        branch=branch,
        month=_month_start(),
        invested_amount=Decimal("0.00"),
        current_balance=balance,
    )


def _api_ids(response):
    data = response.json()["data"]
    return {item["id"] for item in data["results"]}


# ---------------------------------------------------------------------------
# 1. DebtCreateService — service-level permission enforcement
# ---------------------------------------------------------------------------

class TestDebtCreateServicePermissions:
    def test_phone_seller_can_create_phone_debt(self, branches, users):
        _make_capital(models.PhoneCapital, branches["main"])
        debt = DebtCreateService.create_debt(
            branch=branches["main"],
            f_name="Phone Seller Debt",
            amount=Decimal("100.00"),
            direction="WE_GAVE",
            created_by=users["phone_seller"],
        )
        assert debt.domain == models.Debt.DOMAIN_PHONE
        assert debt.branch_id == branches["main"].id

    def test_accessory_seller_can_create_accessory_debt(self, branches, users):
        _make_capital(models.AccessoryCapital, branches["main"])
        debt = DebtCreateService.create_debt(
            branch=branches["main"],
            f_name="Accessory Seller Debt",
            amount=Decimal("50.00"),
            direction="WE_TOOK",
            created_by=users["accessory_seller"],
        )
        assert debt.domain == models.Debt.DOMAIN_ACCESSORY

    def test_owner_cannot_create_debt_via_service(self, branches, users):
        with pytest.raises(PermissionDenied):
            DebtCreateService.create_debt(
                branch=branches["main"],
                f_name="Owner Debt",
                amount=Decimal("100.00"),
                direction="WE_GAVE",
                created_by=users["owner"],
            )

    def test_outsider_cannot_create_debt_via_service(self, branches, users):
        with pytest.raises(PermissionDenied):
            DebtCreateService.create_debt(
                branch=branches["main"],
                f_name="Outsider Debt",
                amount=Decimal("100.00"),
                direction="WE_GAVE",
                created_by=users["outsider"],
            )

    def test_seller_cannot_create_debt_for_another_branch(self, branches, users):
        other_branch = models.Branch.objects.create(
            name="Unrelated Branch",
            owner=users["owner"],
        )
        with pytest.raises(PermissionDenied):
            DebtCreateService.create_debt(
                branch=other_branch,
                f_name="Wrong Branch Debt",
                amount=Decimal("100.00"),
                direction="WE_GAVE",
                created_by=users["phone_seller"],
            )

    def test_none_branch_raises(self, users):
        with pytest.raises(PermissionDenied):
            DebtCreateService.create_debt(
                branch=None,
                f_name="No Branch",
                amount=Decimal("100.00"),
                direction="WE_GAVE",
                created_by=users["phone_seller"],
            )


# ---------------------------------------------------------------------------
# 2. Capital isolation — create / pay / delete
# ---------------------------------------------------------------------------

class TestCapitalIsolation:
    def test_we_gave_phone_create_subtracts_phone_capital_only(self, branches, users):
        phone_cap = _make_capital(models.PhoneCapital, branches["main"], Decimal("1000.00"))
        acc_cap = _make_capital(models.AccessoryCapital, branches["main"], Decimal("1000.00"))

        DebtCreateService.create_debt(
            branch=branches["main"],
            f_name="WE_GAVE Phone",
            amount=Decimal("200.00"),
            direction="WE_GAVE",
            created_by=users["phone_seller"],
        )

        phone_cap.refresh_from_db()
        acc_cap.refresh_from_db()
        assert phone_cap.current_balance == Decimal("800.00")
        assert acc_cap.current_balance == Decimal("1000.00")

    def test_we_took_phone_create_adds_phone_capital_only(self, branches, users):
        phone_cap = _make_capital(models.PhoneCapital, branches["main"], Decimal("1000.00"))
        acc_cap = _make_capital(models.AccessoryCapital, branches["main"], Decimal("1000.00"))

        DebtCreateService.create_debt(
            branch=branches["main"],
            f_name="WE_TOOK Phone",
            amount=Decimal("300.00"),
            direction="WE_TOOK",
            created_by=users["phone_seller"],
        )

        phone_cap.refresh_from_db()
        acc_cap.refresh_from_db()
        assert phone_cap.current_balance == Decimal("1300.00")
        assert acc_cap.current_balance == Decimal("1000.00")

    def test_we_gave_accessory_create_subtracts_accessory_capital_only(self, branches, users):
        phone_cap = _make_capital(models.PhoneCapital, branches["main"], Decimal("1000.00"))
        acc_cap = _make_capital(models.AccessoryCapital, branches["main"], Decimal("1000.00"))

        DebtCreateService.create_debt(
            branch=branches["main"],
            f_name="WE_GAVE Accessory",
            amount=Decimal("150.00"),
            direction="WE_GAVE",
            created_by=users["accessory_seller"],
        )

        phone_cap.refresh_from_db()
        acc_cap.refresh_from_db()
        assert acc_cap.current_balance == Decimal("850.00")
        assert phone_cap.current_balance == Decimal("1000.00")

    def test_we_took_accessory_create_adds_accessory_capital_only(self, branches, users):
        phone_cap = _make_capital(models.PhoneCapital, branches["main"], Decimal("1000.00"))
        acc_cap = _make_capital(models.AccessoryCapital, branches["main"], Decimal("1000.00"))

        DebtCreateService.create_debt(
            branch=branches["main"],
            f_name="WE_TOOK Accessory",
            amount=Decimal("250.00"),
            direction="WE_TOOK",
            created_by=users["accessory_seller"],
        )

        phone_cap.refresh_from_db()
        acc_cap.refresh_from_db()
        assert acc_cap.current_balance == Decimal("1250.00")
        assert phone_cap.current_balance == Decimal("1000.00")

    def test_we_gave_payment_adds_phone_capital(self, branches, users):
        phone_cap = _make_capital(models.PhoneCapital, branches["main"], Decimal("1000.00"))
        debt = DebtCreateService.create_debt(
            branch=branches["main"],
            f_name="Pay Phone WE_GAVE",
            amount=Decimal("200.00"),
            direction="WE_GAVE",
            created_by=users["phone_seller"],
        )
        phone_cap.refresh_from_db()
        assert phone_cap.current_balance == Decimal("800.00")

        DebtPaymentCreateService.create_payment(
            debt=debt, amount=Decimal("50.00"), paid_by=users["phone_seller"], note=""
        )
        phone_cap.refresh_from_db()
        assert phone_cap.current_balance == Decimal("850.00")

    def test_we_took_payment_subtracts_phone_capital(self, branches, users):
        phone_cap = _make_capital(models.PhoneCapital, branches["main"], Decimal("1000.00"))
        debt = DebtCreateService.create_debt(
            branch=branches["main"],
            f_name="Pay Phone WE_TOOK",
            amount=Decimal("300.00"),
            direction="WE_TOOK",
            created_by=users["phone_seller"],
        )
        phone_cap.refresh_from_db()
        assert phone_cap.current_balance == Decimal("1300.00")

        DebtPaymentCreateService.create_payment(
            debt=debt, amount=Decimal("100.00"), paid_by=users["phone_seller"], note=""
        )
        phone_cap.refresh_from_db()
        assert phone_cap.current_balance == Decimal("1200.00")

    def test_we_gave_delete_restores_phone_capital(self, branches, users):
        phone_cap = _make_capital(models.PhoneCapital, branches["main"], Decimal("1000.00"))
        debt = DebtCreateService.create_debt(
            branch=branches["main"],
            f_name="Delete Phone WE_GAVE",
            amount=Decimal("200.00"),
            direction="WE_GAVE",
            created_by=users["phone_seller"],
        )
        phone_cap.refresh_from_db()
        assert phone_cap.current_balance == Decimal("800.00")

        payment = DebtPaymentCreateService.create_payment(
            debt=debt, amount=Decimal("50.00"), paid_by=users["phone_seller"], note=""
        )
        phone_cap.refresh_from_db()
        assert phone_cap.current_balance == Decimal("850.00")

        debt.refresh_from_db()
        DebtDeleteService.delete_debt(debt, deleted_by=users["phone_seller"])
        phone_cap.refresh_from_db()
        # remaining_amount after 50 payment = 150; delete adds 150 back
        assert phone_cap.current_balance == Decimal("1000.00")

    def test_we_took_delete_subtracts_remaining_from_phone_capital(self, branches, users):
        phone_cap = _make_capital(models.PhoneCapital, branches["main"], Decimal("1000.00"))
        debt = DebtCreateService.create_debt(
            branch=branches["main"],
            f_name="Delete Phone WE_TOOK",
            amount=Decimal("300.00"),
            direction="WE_TOOK",
            created_by=users["phone_seller"],
        )
        phone_cap.refresh_from_db()
        assert phone_cap.current_balance == Decimal("1300.00")

        DebtPaymentCreateService.create_payment(
            debt=debt, amount=Decimal("100.00"), paid_by=users["phone_seller"], note=""
        )
        phone_cap.refresh_from_db()
        assert phone_cap.current_balance == Decimal("1200.00")

        debt.refresh_from_db()
        DebtDeleteService.delete_debt(debt, deleted_by=users["phone_seller"])
        phone_cap.refresh_from_db()
        # remaining_amount after 100 payment = 200; delete subtracts 200
        assert phone_cap.current_balance == Decimal("1000.00")

    def test_no_cross_branch_capital_effect(self, branches, users):
        other_branch = models.Branch.objects.create(name="Other B", owner=users["owner"])
        other_seller = models.User.objects.create_user(
            username="other_seller_cap", password="pass"
        )
        models.BranchUser.objects.create(
            user=other_seller,
            branch=other_branch,
            role=models.BranchUser.ROLE_PHONE_SELLER,
        )
        main_cap = _make_capital(models.PhoneCapital, branches["main"], Decimal("1000.00"))
        other_cap = _make_capital(models.PhoneCapital, other_branch, Decimal("500.00"))

        DebtCreateService.create_debt(
            branch=other_branch,
            f_name="Other Branch Debt",
            amount=Decimal("100.00"),
            direction="WE_GAVE",
            created_by=other_seller,
        )

        main_cap.refresh_from_db()
        other_cap.refresh_from_db()
        assert main_cap.current_balance == Decimal("1000.00")
        assert other_cap.current_balance == Decimal("400.00")


# ---------------------------------------------------------------------------
# 3. API — create restrictions
# ---------------------------------------------------------------------------

class TestAPICreatePermissions:
    def test_owner_cannot_create_debt_api(self, api_client, users):
        api_client.force_authenticate(user=users["owner"])
        response = api_client.post(
            reverse("api_debt_list_create"),
            {"f_name": "Owner Attempt", "amount": "100.00", "direction": "WE_GAVE"},
            format="json",
        )
        assert response.status_code == 403
        assert response.json()["success"] is False

    def test_outsider_cannot_create_debt_api(self, api_client, users):
        api_client.force_authenticate(user=users["outsider"])
        response = api_client.post(
            reverse("api_debt_list_create"),
            {"f_name": "Outsider Attempt", "amount": "100.00", "direction": "WE_GAVE"},
            format="json",
        )
        assert response.status_code == 403

    def test_phone_seller_creates_phone_domain_debt(self, api_client, users, branches):
        api_client.force_authenticate(user=users["phone_seller"])
        response = api_client.post(
            reverse("api_debt_list_create"),
            {"f_name": "API Phone Debt", "amount": "200.00", "direction": "WE_GAVE"},
            format="json",
        )
        assert response.status_code == 201
        debt = models.Debt.objects.get(f_name="API Phone Debt")
        assert debt.domain == models.Debt.DOMAIN_PHONE
        assert debt.branch_id == branches["main"].id

    def test_accessory_seller_creates_accessory_domain_debt(self, api_client, users, branches):
        api_client.force_authenticate(user=users["accessory_seller"])
        response = api_client.post(
            reverse("api_debt_list_create"),
            {"f_name": "API Accessory Debt", "amount": "75.00", "direction": "WE_TOOK"},
            format="json",
        )
        assert response.status_code == 201
        debt = models.Debt.objects.get(f_name="API Accessory Debt")
        assert debt.domain == models.Debt.DOMAIN_ACCESSORY
        assert debt.branch_id == branches["main"].id


# ---------------------------------------------------------------------------
# 4. API — domain filtering (see/pay/delete)
# ---------------------------------------------------------------------------

class TestAPIDomainFiltering:
    def test_phone_seller_cannot_see_accessory_debt(
        self, api_client, users, branches, debt_factory
    ):
        acc_debt = debt_factory(
            branch=branches["main"],
            created_by=users["accessory_seller"],
            domain=models.Debt.DOMAIN_ACCESSORY,
            f_name="Accessory Only",
        )
        api_client.force_authenticate(user=users["phone_seller"])
        response = api_client.get(reverse("api_debt_list_create"))
        assert response.status_code == 200
        assert acc_debt.id not in _api_ids(response)

    def test_accessory_seller_cannot_see_phone_debt(
        self, api_client, users, branches, debt_factory
    ):
        phone_debt = debt_factory(
            branch=branches["main"],
            created_by=users["phone_seller"],
            domain=models.Debt.DOMAIN_PHONE,
            f_name="Phone Only",
        )
        api_client.force_authenticate(user=users["accessory_seller"])
        response = api_client.get(reverse("api_debt_list_create"))
        assert response.status_code == 200
        assert phone_debt.id not in _api_ids(response)

    def test_phone_seller_cannot_pay_accessory_debt(
        self, api_client, users, branches, debt_factory
    ):
        acc_debt = debt_factory(
            branch=branches["main"],
            created_by=users["accessory_seller"],
            domain=models.Debt.DOMAIN_ACCESSORY,
            f_name="Blocked Pay",
            remaining_amount=Decimal("100.00"),
        )
        api_client.force_authenticate(user=users["phone_seller"])
        response = api_client.post(
            reverse("api_debt_pay", args=[acc_debt.id]),
            {"amount": "10.00", "note": "Blocked"},
            format="json",
        )
        assert response.status_code == 403
        assert not models.DebtPayment.objects.filter(
            debt=acc_debt, is_deleted=False
        ).exists()

    def test_accessory_seller_cannot_pay_phone_debt(
        self, api_client, users, branches, debt_factory
    ):
        phone_debt = debt_factory(
            branch=branches["main"],
            created_by=users["phone_seller"],
            domain=models.Debt.DOMAIN_PHONE,
            f_name="Blocked Pay Phone",
            remaining_amount=Decimal("100.00"),
        )
        api_client.force_authenticate(user=users["accessory_seller"])
        response = api_client.post(
            reverse("api_debt_pay", args=[phone_debt.id]),
            {"amount": "10.00", "note": "Blocked"},
            format="json",
        )
        assert response.status_code == 403

    def test_phone_seller_cannot_delete_accessory_debt(
        self, api_client, users, branches, debt_factory
    ):
        acc_debt = debt_factory(
            branch=branches["main"],
            created_by=users["accessory_seller"],
            domain=models.Debt.DOMAIN_ACCESSORY,
            f_name="Cannot Delete",
        )
        api_client.force_authenticate(user=users["phone_seller"])
        response = api_client.delete(reverse("api_debt_delete", args=[acc_debt.id]))
        assert response.status_code == 403
        acc_debt.refresh_from_db()
        assert acc_debt.is_deleted is False

    def test_accessory_seller_cannot_delete_phone_debt(
        self, api_client, users, branches, debt_factory
    ):
        phone_debt = debt_factory(
            branch=branches["main"],
            created_by=users["phone_seller"],
            domain=models.Debt.DOMAIN_PHONE,
            f_name="Cannot Delete Phone",
        )
        api_client.force_authenticate(user=users["accessory_seller"])
        response = api_client.delete(reverse("api_debt_delete", args=[phone_debt.id]))
        assert response.status_code == 403
        phone_debt.refresh_from_db()
        assert phone_debt.is_deleted is False

    def test_same_domain_seller_can_see_peer_debt(
        self, api_client, users, branches, debt_factory
    ):
        peer = models.User.objects.create_user(username="peer_phone_parity", password="pass")
        models.BranchUser.objects.create(
            user=peer,
            branch=branches["main"],
            role=models.BranchUser.ROLE_PHONE_SELLER,
        )
        peer_debt = debt_factory(
            branch=branches["main"],
            created_by=peer,
            domain=models.Debt.DOMAIN_PHONE,
            f_name="Peer Phone Debt",
        )
        api_client.force_authenticate(user=users["phone_seller"])
        response = api_client.get(reverse("api_debt_list_create"))
        assert peer_debt.id in _api_ids(response)

    def test_same_domain_seller_can_pay_peer_debt(
        self, api_client, users, branches, debt_factory
    ):
        peer = models.User.objects.create_user(username="peer_phone_pay", password="pass")
        models.BranchUser.objects.create(
            user=peer,
            branch=branches["main"],
            role=models.BranchUser.ROLE_PHONE_SELLER,
        )
        peer_debt = debt_factory(
            branch=branches["main"],
            created_by=peer,
            domain=models.Debt.DOMAIN_PHONE,
            f_name="Peer Pay Debt",
            remaining_amount=Decimal("100.00"),
        )
        api_client.force_authenticate(user=users["phone_seller"])
        response = api_client.post(
            reverse("api_debt_pay", args=[peer_debt.id]),
            {"amount": "20.00", "note": "Peer pay"},
            format="json",
        )
        assert response.status_code == 200

    def test_seller_cannot_delete_peer_debt(
        self, api_client, users, branches, debt_factory
    ):
        """Seller may only delete debts they created, not peer's debts."""
        peer = models.User.objects.create_user(username="peer_phone_del", password="pass")
        models.BranchUser.objects.create(
            user=peer,
            branch=branches["main"],
            role=models.BranchUser.ROLE_PHONE_SELLER,
        )
        peer_debt = debt_factory(
            branch=branches["main"],
            created_by=peer,
            domain=models.Debt.DOMAIN_PHONE,
            f_name="Peer Delete Debt",
        )
        api_client.force_authenticate(user=users["phone_seller"])
        response = api_client.delete(reverse("api_debt_delete", args=[peer_debt.id]))
        assert response.status_code == 403
        peer_debt.refresh_from_db()
        assert peer_debt.is_deleted is False


# ---------------------------------------------------------------------------
# 5. API — owner delete rules
# ---------------------------------------------------------------------------

class TestAPIOwnerDelete:
    def test_owner_can_delete_current_month_debt_in_owned_branch(
        self, api_client, users, branches, debt_factory
    ):
        debt = debt_factory(
            branch=branches["main"],
            created_by=users["phone_seller"],
            domain=models.Debt.DOMAIN_PHONE,
            f_name="Owner Can Delete",
        )
        api_client.force_authenticate(user=users["owner"])
        response = api_client.delete(reverse("api_debt_delete", args=[debt.id]))
        assert response.status_code == 200
        debt.refresh_from_db()
        assert debt.is_deleted is True

    def test_owner_cannot_delete_debt_from_unowned_branch(
        self, api_client, users, debt_factory
    ):
        other_owner = models.User.objects.create_user(
            username="other_owner_del", password="pass"
        )
        other_branch = models.Branch.objects.create(
            name="Unowned Branch", owner=other_owner
        )
        models.BranchUser.objects.create(
            user=other_owner,
            branch=other_branch,
            role=models.BranchUser.ROLE_OWNER,
        )
        other_seller = models.User.objects.create_user(
            username="other_seller_del", password="pass"
        )
        models.BranchUser.objects.create(
            user=other_seller,
            branch=other_branch,
            role=models.BranchUser.ROLE_PHONE_SELLER,
        )
        debt = debt_factory(
            branch=other_branch,
            created_by=other_seller,
            domain=models.Debt.DOMAIN_PHONE,
            f_name="Unowned Debt",
        )
        api_client.force_authenticate(user=users["owner"])
        response = api_client.delete(reverse("api_debt_delete", args=[debt.id]))
        assert response.status_code == 403
        debt.refresh_from_db()
        assert debt.is_deleted is False

    def test_past_month_debt_delete_blocked(
        self, api_client, users, debt_factory, set_model_datetime, time_points
    ):
        debt = debt_factory(f_name="Past Month Delete")
        set_model_datetime(
            debt, added_at=time_points["previous"], updated_at=time_points["previous"]
        )
        api_client.force_authenticate(user=users["owner"])
        response = api_client.delete(reverse("api_debt_delete", args=[debt.id]))
        assert response.status_code == 403
        debt.refresh_from_db()
        assert debt.is_deleted is False

    def test_past_month_debt_payment_blocked(
        self, api_client, users, debt_factory, set_model_datetime, time_points
    ):
        debt = debt_factory(f_name="Past Month Pay", remaining_amount=Decimal("80.00"))
        set_model_datetime(
            debt, added_at=time_points["previous"], updated_at=time_points["previous"]
        )
        api_client.force_authenticate(user=users["owner"])
        response = api_client.post(
            reverse("api_debt_pay", args=[debt.id]),
            {"amount": "10.00"},
            format="json",
        )
        assert response.status_code == 403


# ---------------------------------------------------------------------------
# 6. API — payment amount validation
# ---------------------------------------------------------------------------

class TestAPIPaymentValidation:
    def test_payment_cannot_exceed_remaining_amount(
        self, api_client, users, debt_factory
    ):
        debt = debt_factory(f_name="Limited Debt", remaining_amount=Decimal("30.00"))
        api_client.force_authenticate(user=users["owner"])
        response = api_client.post(
            reverse("api_debt_pay", args=[debt.id]),
            {"amount": "50.00"},
            format="json",
        )
        assert response.status_code == 400
        assert response.json()["success"] is False


# ---------------------------------------------------------------------------
# 7. API — closed debt list
# ---------------------------------------------------------------------------

class TestAPIClosedDebtList:
    def test_closed_debt_list_shows_fully_paid_debts(
        self, api_client, users, branches, debt_factory
    ):
        open_debt = debt_factory(
            branch=branches["main"],
            created_by=users["phone_seller"],
            domain=models.Debt.DOMAIN_PHONE,
            f_name="Open Debt",
            amount=Decimal("100.00"),
            remaining_amount=Decimal("50.00"),
        )
        closed_debt = debt_factory(
            branch=branches["main"],
            created_by=users["phone_seller"],
            domain=models.Debt.DOMAIN_PHONE,
            f_name="Closed Debt",
            amount=Decimal("100.00"),
            remaining_amount=Decimal("0.00"),
        )
        models.DebtPayment.objects.create(
            debt=closed_debt,
            amount=Decimal("100.00"),
            remaining_balance=Decimal("0.00"),
            paid_by=users["phone_seller"],
            note="Full payment",
        )

        api_client.force_authenticate(user=users["phone_seller"])
        response = api_client.get(reverse("api_debt_closed_list"))
        assert response.status_code == 200
        ids = _api_ids(response)
        assert closed_debt.id in ids
        assert open_debt.id not in ids

    def test_open_debt_list_excludes_fully_paid_debts(
        self, api_client, users, branches, debt_factory
    ):
        fully_paid = debt_factory(
            branch=branches["main"],
            created_by=users["phone_seller"],
            domain=models.Debt.DOMAIN_PHONE,
            f_name="Full Paid",
            amount=Decimal("100.00"),
            remaining_amount=Decimal("0.00"),
        )
        models.DebtPayment.objects.create(
            debt=fully_paid,
            amount=Decimal("100.00"),
            remaining_balance=Decimal("0.00"),
            paid_by=users["phone_seller"],
            note="Done",
        )
        api_client.force_authenticate(user=users["phone_seller"])
        response = api_client.get(reverse("api_debt_list_create"))
        assert fully_paid.id not in _api_ids(response)


# ---------------------------------------------------------------------------
# 8. API — payment delete: owner-only policy
# ---------------------------------------------------------------------------

class TestAPIPaymentDeletePolicy:
    def _create_payment(self, debt, paid_by, amount=Decimal("20.00")):
        return models.DebtPayment.objects.create(
            debt=debt,
            amount=amount,
            remaining_balance=Decimal("0.00"),
            paid_by=paid_by,
            note="test",
        )

    def test_owner_can_delete_payment_in_owned_branch(
        self, api_client, users, branches, debt_factory
    ):
        debt = debt_factory(
            branch=branches["main"],
            domain=models.Debt.DOMAIN_PHONE,
            remaining_amount=Decimal("80.00"),
        )
        payment = self._create_payment(debt, users["phone_seller"])
        api_client.force_authenticate(user=users["owner"])
        response = api_client.delete(
            reverse("api_debt_payment_delete", args=[payment.id])
        )
        assert response.status_code == 200
        assert models.DebtPayment.objects.filter(pk=payment.id, is_deleted=False).exists() is False

    def test_seller_cannot_delete_payment_via_api(
        self, api_client, users, branches, debt_factory
    ):
        debt = debt_factory(
            branch=branches["main"],
            domain=models.Debt.DOMAIN_PHONE,
            remaining_amount=Decimal("80.00"),
        )
        payment = self._create_payment(debt, users["phone_seller"])
        api_client.force_authenticate(user=users["phone_seller"])
        response = api_client.delete(
            reverse("api_debt_payment_delete", args=[payment.id])
        )
        assert response.status_code == 403
        assert models.DebtPayment.objects.filter(pk=payment.id, is_deleted=False).exists()

    def test_owner_cannot_delete_payment_in_unowned_branch(
        self, api_client, users, debt_factory
    ):
        other_owner = models.User.objects.create_user(
            username="unowned_owner_pay", password="pass"
        )
        other_branch = models.Branch.objects.create(
            name="Unowned Pay Branch", owner=other_owner
        )
        models.BranchUser.objects.create(
            user=other_owner, branch=other_branch, role=models.BranchUser.ROLE_OWNER
        )
        other_seller = models.User.objects.create_user(
            username="unowned_seller_pay", password="pass"
        )
        models.BranchUser.objects.create(
            user=other_seller,
            branch=other_branch,
            role=models.BranchUser.ROLE_PHONE_SELLER,
        )
        debt = debt_factory(
            branch=other_branch,
            created_by=other_seller,
            domain=models.Debt.DOMAIN_PHONE,
        )
        payment = self._create_payment(debt, other_seller)
        api_client.force_authenticate(user=users["owner"])
        response = api_client.delete(
            reverse("api_debt_payment_delete", args=[payment.id])
        )
        assert response.status_code == 403
        assert models.DebtPayment.objects.filter(pk=payment.id, is_deleted=False).exists()


# ---------------------------------------------------------------------------
# 9. Web — create view restrictions
# ---------------------------------------------------------------------------

class TestWebCreatePermissions:
    def test_owner_cannot_access_web_create_view(self, client, users, branches):
        client.force_login(users["owner"])
        response = client.get(reverse("debt_create"))
        # should redirect to dashboard (403 via _deny)
        assert response.status_code == 302
        assert "dashboard" in response["Location"]

    def test_owner_post_to_web_create_is_rejected(self, client, users, branches):
        client.force_login(users["owner"])
        response = client.post(
            reverse("debt_create"),
            {
                "f_name": "Owner Web Debt",
                "amount": "100.00",
                "direction": "WE_GAVE",
                "note": "",
            },
        )
        assert response.status_code == 302
        assert not models.Debt.objects.filter(f_name="Owner Web Debt").exists()

    def test_outsider_cannot_access_web_create_view(self, client, users):
        client.force_login(users["outsider"])
        response = client.get(reverse("debt_create"))
        assert response.status_code == 302
        assert "dashboard" in response["Location"]

    def test_phone_seller_can_access_web_create_view(self, client, users, branches):
        client.force_login(users["phone_seller"])
        response = client.get(reverse("debt_create"))
        assert response.status_code == 200

    def test_web_create_assigns_seller_branch_not_form_branch(
        self, client, users, branches
    ):
        """Branch comes from seller profile, ignoring any branch field in POST."""
        client.force_login(users["phone_seller"])
        response = client.post(
            reverse("debt_create"),
            {
                "f_name": "Web Branch Test",
                "amount": "100.00",
                "direction": "WE_GAVE",
                "note": "",
            },
            follow=True,
        )
        debt = models.Debt.objects.filter(f_name="Web Branch Test").first()
        if debt:
            assert debt.branch_id == branches["main"].id


# ---------------------------------------------------------------------------
# 10. Web — payment delete view: owner-only policy
# ---------------------------------------------------------------------------

class TestWebPaymentDeletePolicy:
    def _make_debt_and_payment(self, branch, seller, paid_by, domain):
        debt = models.Debt.objects.create(
            branch=branch,
            created_by=seller,
            f_name="Web Pay Delete Test",
            amount=Decimal("100.00"),
            remaining_amount=Decimal("80.00"),
            direction="WE_GAVE",
            domain=domain,
        )
        payment = models.DebtPayment.objects.create(
            debt=debt,
            amount=Decimal("20.00"),
            remaining_balance=Decimal("80.00"),
            paid_by=paid_by,
            note="test",
        )
        return debt, payment

    def test_seller_cannot_delete_payment_via_web(self, client, users, branches):
        client.force_login(users["phone_seller"])
        debt, payment = self._make_debt_and_payment(
            branches["main"],
            users["phone_seller"],
            users["phone_seller"],
            models.Debt.DOMAIN_PHONE,
        )
        response = client.get(reverse("debt_payment_delete", args=[payment.id]))
        # seller has no permission → redirected to dashboard
        assert response.status_code == 302
        assert "dashboard" in response["Location"]

    def test_seller_post_delete_payment_is_rejected(self, client, users, branches):
        client.force_login(users["phone_seller"])
        debt, payment = self._make_debt_and_payment(
            branches["main"],
            users["phone_seller"],
            users["phone_seller"],
            models.Debt.DOMAIN_PHONE,
        )
        response = client.post(reverse("debt_payment_delete", args=[payment.id]))
        assert response.status_code == 302
        assert models.DebtPayment.objects.filter(pk=payment.id, is_deleted=False).exists()

    def test_owner_can_delete_payment_via_web(self, client, users, branches):
        client.force_login(users["owner"])
        debt, payment = self._make_debt_and_payment(
            branches["main"],
            users["phone_seller"],
            users["phone_seller"],
            models.Debt.DOMAIN_PHONE,
        )
        response = client.post(
            reverse("debt_payment_delete", args=[payment.id]), follow=True
        )
        assert response.status_code == 200
        assert models.DebtPayment.objects.filter(pk=payment.id, is_deleted=False).exists() is False

    def test_owner_cannot_delete_payment_in_unowned_branch_web(self, client, users):
        other_owner = models.User.objects.create_user(
            username="unowned_web_owner", password="pass"
        )
        other_branch = models.Branch.objects.create(
            name="Unowned Web Branch", owner=other_owner
        )
        models.BranchUser.objects.create(
            user=other_owner, branch=other_branch, role=models.BranchUser.ROLE_OWNER
        )
        other_seller = models.User.objects.create_user(
            username="unowned_web_seller", password="pass"
        )
        models.BranchUser.objects.create(
            user=other_seller,
            branch=other_branch,
            role=models.BranchUser.ROLE_PHONE_SELLER,
        )
        debt, payment = self._make_debt_and_payment(
            other_branch,
            other_seller,
            other_seller,
            models.Debt.DOMAIN_PHONE,
        )
        client.force_login(users["owner"])
        response = client.post(reverse("debt_payment_delete", args=[payment.id]))
        assert response.status_code == 302
        assert models.DebtPayment.objects.filter(pk=payment.id, is_deleted=False).exists()


# ---------------------------------------------------------------------------
# 11. API — owner branch filter
# ---------------------------------------------------------------------------

class TestAPIOwnerBranchFilter:
    def test_owner_branch_filter_works(self, api_client, users, branches, debt_factory):
        models.BranchUser.objects.get_or_create(
            user=users["owner"],
            branch=branches["other"],
            defaults={"role": models.BranchUser.ROLE_OWNER},
        )
        other_seller = models.User.objects.create_user(
            username="other_br_seller", password="pass"
        )
        models.BranchUser.objects.create(
            user=other_seller,
            branch=branches["other"],
            role=models.BranchUser.ROLE_PHONE_SELLER,
        )
        main_debt = debt_factory(
            branch=branches["main"],
            created_by=users["phone_seller"],
            domain=models.Debt.DOMAIN_PHONE,
            f_name="Main Branch Debt Filter",
        )
        other_debt = debt_factory(
            branch=branches["other"],
            created_by=other_seller,
            domain=models.Debt.DOMAIN_PHONE,
            f_name="Other Branch Debt Filter",
        )
        api_client.force_authenticate(user=users["owner"])
        response = api_client.get(
            reverse("api_debt_list_create"), {"branch": branches["other"].id}
        )
        assert response.status_code == 200
        ids = _api_ids(response)
        assert other_debt.id in ids
        assert main_debt.id not in ids

    def test_owner_can_list_all_owned_branch_debts(
        self, api_client, users, branches, debt_factory
    ):
        phone_debt = debt_factory(
            branch=branches["main"],
            created_by=users["phone_seller"],
            domain=models.Debt.DOMAIN_PHONE,
            f_name="Phone Owner List",
        )
        acc_debt = debt_factory(
            branch=branches["main"],
            created_by=users["accessory_seller"],
            domain=models.Debt.DOMAIN_ACCESSORY,
            f_name="Accessory Owner List",
        )
        api_client.force_authenticate(user=users["owner"])
        response = api_client.get(reverse("api_debt_list_create"))
        ids = _api_ids(response)
        assert phone_debt.id in ids
        assert acc_debt.id in ids


# ---------------------------------------------------------------------------
# 12. Search filter
# ---------------------------------------------------------------------------

class TestAPISearchFilter:
    def test_search_by_f_name_works(self, api_client, users, branches, debt_factory):
        matching = debt_factory(
            branch=branches["main"],
            created_by=users["phone_seller"],
            domain=models.Debt.DOMAIN_PHONE,
            f_name="Unique SearchName XYZ",
        )
        other = debt_factory(
            branch=branches["main"],
            created_by=users["phone_seller"],
            domain=models.Debt.DOMAIN_PHONE,
            f_name="Different Name",
        )
        api_client.force_authenticate(user=users["phone_seller"])
        response = api_client.get(reverse("api_debt_list_create"), {"q": "SearchName XYZ"})
        assert response.status_code == 200
        ids = _api_ids(response)
        assert matching.id in ids
        assert other.id not in ids


# ---------------------------------------------------------------------------
# 13. Direction filter
# ---------------------------------------------------------------------------

class TestAPIDirectionFilter:
    def test_filter_by_direction_we_gave(self, api_client, users, branches, debt_factory):
        we_gave = debt_factory(
            branch=branches["main"],
            created_by=users["phone_seller"],
            domain=models.Debt.DOMAIN_PHONE,
            direction="WE_GAVE",
            f_name="We Gave Debt",
        )
        we_took = debt_factory(
            branch=branches["main"],
            created_by=users["phone_seller"],
            domain=models.Debt.DOMAIN_PHONE,
            direction="WE_TOOK",
            f_name="We Took Debt",
        )
        api_client.force_authenticate(user=users["phone_seller"])
        response = api_client.get(
            reverse("api_debt_list_create"), {"type": "WE_GAVE"}
        )
        ids = _api_ids(response)
        assert we_gave.id in ids
        assert we_took.id not in ids

    def test_filter_by_direction_we_took(self, api_client, users, branches, debt_factory):
        we_gave = debt_factory(
            branch=branches["main"],
            created_by=users["phone_seller"],
            domain=models.Debt.DOMAIN_PHONE,
            direction="WE_GAVE",
            f_name="Filter WE_GAVE",
        )
        we_took = debt_factory(
            branch=branches["main"],
            created_by=users["phone_seller"],
            domain=models.Debt.DOMAIN_PHONE,
            direction="WE_TOOK",
            f_name="Filter WE_TOOK",
        )
        api_client.force_authenticate(user=users["phone_seller"])
        response = api_client.get(
            reverse("api_debt_list_create"), {"type": "WE_TOOK"}
        )
        ids = _api_ids(response)
        assert we_took.id in ids
        assert we_gave.id not in ids
