"""Debt API tests."""

from decimal import Decimal

import pytest
from django.urls import reverse
from django.utils import timezone

from src.core import models


pytestmark = pytest.mark.django_db


def _payload(response):
    payload = response.json()
    assert payload["success"] is True
    data = payload["data"]
    assert "count" in data
    assert "next" in data
    assert "previous" in data
    assert "results" in data
    assert len(data["results"]) <= 20
    return data


def test_seller_can_create_debt(api_client, users, branches):
    """Seller can create debt and branch is auto assigned."""
    api_client.force_authenticate(user=users["phone_seller"])

    response = api_client.post(
        reverse("api_debt_list_create"),
        {
            "f_name": "Seller Debt",
            "amount": "120.00",
            "direction": "WE_GAVE",
            "note": "Created from API",
        },
        format="json",
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["success"] is True

    debt = models.Debt.objects.get(f_name="Seller Debt")
    assert debt.branch_id == branches["main"].id
    assert debt.created_by_id == users["phone_seller"].id
    assert debt.domain == models.Debt.DOMAIN_PHONE
    assert debt.remaining_amount == Decimal("120.00")


def test_owner_cannot_create_debt(api_client, users):
    """Owner cannot create debt through the API."""
    api_client.force_authenticate(user=users["owner"])

    response = api_client.post(
        reverse("api_debt_list_create"),
        {
            "f_name": "Owner Debt",
            "amount": "100.00",
            "direction": "WE_GAVE",
        },
        format="json",
    )

    assert response.status_code == 403
    assert response.json()["success"] is False


def test_payment_updates_correct_capital(api_client, users, branches):
    """Debt payment updates capital based on original debt type."""
    month_start = timezone.now().date().replace(day=1)
    phone_capital = models.PhoneCapital.objects.create(
        branch=branches["main"],
        month=month_start,
        invested_amount=Decimal("0.00"),
        current_balance=Decimal("1000.00"),
    )
    accessory_capital = models.AccessoryCapital.objects.create(
        branch=branches["main"],
        month=month_start,
        invested_amount=Decimal("0.00"),
        current_balance=Decimal("1000.00"),
    )

    api_client.force_authenticate(user=users["phone_seller"])
    create_response = api_client.post(
        reverse("api_debt_list_create"),
        {
            "f_name": "Phone Capital Debt",
            "amount": "200.00",
            "direction": "WE_GAVE",
            "note": "Phone debt",
        },
        format="json",
    )
    debt_id = create_response.json()["data"]["id"]

    phone_capital.refresh_from_db()
    accessory_capital.refresh_from_db()
    assert phone_capital.current_balance == Decimal("800.00")
    assert accessory_capital.current_balance == Decimal("1000.00")

    api_client.force_authenticate(user=users["owner"])
    pay_response = api_client.post(
        reverse("api_debt_pay", args=[debt_id]),
        {"amount": "50.00", "note": "Owner payment"},
        format="json",
    )

    assert pay_response.status_code == 200
    phone_capital.refresh_from_db()
    accessory_capital.refresh_from_db()
    assert phone_capital.current_balance == Decimal("850.00")
    assert accessory_capital.current_balance == Decimal("1000.00")


def test_no_cross_branch_access(api_client, users, debt_factory, branches):
    """Seller cannot see or pay other-branch debts."""
    own_debt = debt_factory(f_name="Own Branch Debt")
    other_branch_debt = debt_factory(
        branch=branches["other"],
        created_by=users["owner"],
        f_name="Other Branch Debt",
    )
    api_client.force_authenticate(user=users["phone_seller"])

    list_response = api_client.get(reverse("api_debt_list_create"))
    assert list_response.status_code == 200
    result_ids = _result_ids(list_response)
    assert own_debt.id in result_ids
    assert other_branch_debt.id not in result_ids

    pay_response = api_client.post(
        reverse("api_debt_pay", args=[other_branch_debt.id]),
        {"amount": "10.00", "note": "Blocked"},
        format="json",
    )
    assert pay_response.status_code == 403
    assert not models.DebtPayment.objects.filter(
        debt=other_branch_debt,
        note="Blocked",
        is_deleted=False,
    ).exists()


def test_list_defaults_to_current_month_and_filters_by_debt_month(
    api_client,
    users,
    debt_factory,
    set_model_datetime,
    time_points,
):
    """Debt list is isolated to the selected debt month."""
    current_debt = debt_factory(f_name="Current Debt")
    previous_debt = debt_factory(f_name="Previous Debt")
    closed_debt = debt_factory(
        f_name="Closed Debt",
        remaining_amount=Decimal("0.00"),
    )
    set_model_datetime(
        current_debt,
        added_at=time_points["current"],
        updated_at=time_points["current"],
    )
    set_model_datetime(
        previous_debt,
        added_at=time_points["previous"],
        updated_at=time_points["previous"],
    )
    set_model_datetime(
        closed_debt,
        added_at=time_points["current"],
        updated_at=time_points["current"],
    )

    api_client.force_authenticate(user=users["phone_seller"])

    default_response = api_client.get(reverse("api_debt_list_create"))
    default_ids = _result_ids(default_response)
    assert current_debt.id in default_ids
    assert previous_debt.id not in default_ids
    assert closed_debt.id not in default_ids

    filtered_response = api_client.get(
        reverse("api_debt_list_create"),
        {
            "year": str(time_points["previous"].year),
            "month": str(time_points["previous"].month),
        },
    )
    filtered_ids = _result_ids(filtered_response)
    assert previous_debt.id in filtered_ids
    assert current_debt.id not in filtered_ids


def test_past_month_debt_cannot_be_paid(api_client, users, debt_factory, set_model_datetime, time_points):
    debt = debt_factory(f_name="Old Debt", remaining_amount=Decimal("80.00"))
    set_model_datetime(
        debt,
        added_at=time_points["previous"],
        updated_at=time_points["previous"],
    )

    api_client.force_authenticate(user=users["owner"])
    response = api_client.post(
        reverse("api_debt_pay", args=[debt.id]),
        {"amount": "10.00", "note": "Blocked old month"},
        format="json",
    )

    assert response.status_code == 403
    assert not models.DebtPayment.objects.filter(
        debt=debt,
        note="Blocked old month",
        is_deleted=False,
    ).exists()


def test_pagination_works(api_client, users, debt_factory):
    """Debt list pagination uses the standard page size."""
    for index in range(21):
        debt_factory(f_name=f"Debt {index}")

    api_client.force_authenticate(user=users["phone_seller"])
    response = api_client.get(reverse("api_debt_list_create"), {"page": 2})

    assert response.status_code == 200
    payload = _payload(response)
    assert payload["count"] == 21
    assert payload["next"] is None
    assert payload["previous"] is not None
    assert len(payload["results"]) == 1


def test_overpayment_is_blocked(api_client, users, debt_factory):
    """Debt payments cannot exceed the remaining balance."""
    debt = debt_factory(f_name="Limited Debt", remaining_amount=Decimal("30.00"))
    api_client.force_authenticate(user=users["owner"])

    response = api_client.post(
        reverse("api_debt_pay", args=[debt.id]),
        {"amount": "50.00", "note": "Too much"},
        format="json",
    )

    assert response.status_code == 400
    assert response.json()["success"] is False
    assert "amount" in response.json()["error"]


def _result_ids(response):
    return {item["id"] for item in _payload(response)["results"]}


def test_phone_seller_sees_only_phone_debts_in_own_branch(api_client, users, branches, debt_factory):
    other_phone_seller = models.User.objects.create_user(username="other_phone_seller", password="pass123")
    models.BranchUser.objects.create(
        user=other_phone_seller,
        branch=branches["main"],
        role=models.BranchUser.ROLE_PHONE_SELLER,
    )

    phone_debt = debt_factory(
        branch=branches["main"],
        created_by=users["phone_seller"],
        domain=models.Debt.DOMAIN_PHONE,
        f_name="Phone Debt",
    )
    other_seller_phone_debt = debt_factory(
        branch=branches["main"],
        created_by=other_phone_seller,
        domain=models.Debt.DOMAIN_PHONE,
        f_name="Other Seller Phone Debt",
    )
    accessory_debt = debt_factory(
        branch=branches["main"],
        created_by=users["accessory_seller"],
        domain=models.Debt.DOMAIN_ACCESSORY,
        f_name="Accessory Debt",
    )
    other_branch_phone_debt = debt_factory(
        branch=branches["other"],
        created_by=users["owner"],
        domain=models.Debt.DOMAIN_PHONE,
        f_name="Other Branch Phone Debt",
    )

    api_client.force_authenticate(user=users["phone_seller"])
    response = api_client.get(reverse("api_debt_list_create"))

    assert response.status_code == 200
    ids = _result_ids(response)
    assert phone_debt.id in ids
    assert other_seller_phone_debt.id in ids
    assert accessory_debt.id not in ids
    assert other_branch_phone_debt.id not in ids


def test_accessory_seller_sees_only_accessory_debts_in_own_branch(api_client, users, branches, debt_factory):
    phone_debt = debt_factory(
        branch=branches["main"],
        created_by=users["phone_seller"],
        domain=models.Debt.DOMAIN_PHONE,
        f_name="Phone Debt",
    )
    accessory_debt = debt_factory(
        branch=branches["main"],
        created_by=users["accessory_seller"],
        domain=models.Debt.DOMAIN_ACCESSORY,
        f_name="Accessory Debt",
    )

    api_client.force_authenticate(user=users["accessory_seller"])
    response = api_client.get(reverse("api_debt_list_create"))

    assert response.status_code == 200
    ids = _result_ids(response)
    assert accessory_debt.id in ids
    assert phone_debt.id not in ids


def test_owner_sees_all_debts_in_own_branches_only(api_client, users, branches, debt_factory):
    phone_main = debt_factory(
        branch=branches["main"],
        created_by=users["phone_seller"],
        domain=models.Debt.DOMAIN_PHONE,
        f_name="Phone Main",
    )
    accessory_main = debt_factory(
        branch=branches["main"],
        created_by=users["accessory_seller"],
        domain=models.Debt.DOMAIN_ACCESSORY,
        f_name="Accessory Main",
    )
    other_branch_debt = debt_factory(
        branch=branches["other"],
        created_by=users["owner"],
        domain=models.Debt.DOMAIN_PHONE,
        f_name="Other Branch Debt",
    )

    other_owner = models.User.objects.create_user(username="other_owner", password="pass123")
    other_branch = models.Branch.objects.create(name="Other Owner Branch", owner=other_owner)
    models.BranchUser.objects.create(
        user=other_owner,
        branch=other_branch,
        role=models.BranchUser.ROLE_OWNER,
    )
    other_owner_debt = debt_factory(
        branch=other_branch,
        created_by=other_owner,
        domain=models.Debt.DOMAIN_PHONE,
        f_name="Other Owner Debt",
    )

    api_client.force_authenticate(user=users["owner"])
    response = api_client.get(reverse("api_debt_list_create"))

    assert response.status_code == 200
    ids = _result_ids(response)
    assert phone_main.id in ids
    assert accessory_main.id in ids
    assert other_branch_debt.id not in ids
    assert other_owner_debt.id not in ids


def test_owner_can_filter_debts_by_owned_branch(api_client, users, branches, debt_factory):
    models.BranchUser.objects.create(
        user=users["owner"],
        branch=branches["other"],
        role=models.BranchUser.ROLE_OWNER,
    )
    main_debt = debt_factory(
        branch=branches["main"],
        created_by=users["phone_seller"],
        domain=models.Debt.DOMAIN_PHONE,
        f_name="Main Branch Debt",
    )
    other_debt = debt_factory(
        branch=branches["other"],
        created_by=users["owner"],
        domain=models.Debt.DOMAIN_PHONE,
        f_name="Other Branch Debt",
    )

    api_client.force_authenticate(user=users["owner"])
    response = api_client.get(
        reverse("api_debt_list_create"),
        {"branch": branches["other"].id},
    )

    assert response.status_code == 200
    ids = _result_ids(response)
    assert other_debt.id in ids
    assert main_debt.id not in ids


def test_current_month_filter_works(api_client, users, debt_factory, set_model_datetime, time_points):
    current_debt = debt_factory(f_name="Debt Current", domain=models.Debt.DOMAIN_PHONE)
    previous_debt = debt_factory(f_name="Debt Previous", domain=models.Debt.DOMAIN_PHONE)
    set_model_datetime(
        current_debt,
        added_at=time_points["current"],
        updated_at=time_points["current"],
    )
    set_model_datetime(
        previous_debt,
        added_at=time_points["previous"],
        updated_at=time_points["previous"],
    )

    api_client.force_authenticate(user=users["owner"])
    response = api_client.get(reverse("api_debt_list_create"))

    assert response.status_code == 200
    ids = _result_ids(response)
    assert current_debt.id in ids
    assert previous_debt.id not in ids


def test_debt_delete_only_current_month(api_client, users, debt_factory, set_model_datetime, time_points):
    current_debt = debt_factory(f_name="Delete Current", domain=models.Debt.DOMAIN_PHONE)
    past_debt = debt_factory(f_name="Delete Past", domain=models.Debt.DOMAIN_PHONE)
    set_model_datetime(
        current_debt,
        added_at=time_points["current"],
        updated_at=time_points["current"],
    )
    set_model_datetime(
        past_debt,
        added_at=time_points["previous"],
        updated_at=time_points["previous"],
    )

    api_client.force_authenticate(user=users["owner"])

    past_response = api_client.delete(reverse("api_debt_delete", args=[past_debt.id]))
    assert past_response.status_code == 403

    current_response = api_client.delete(reverse("api_debt_delete", args=[current_debt.id]))
    assert current_response.status_code == 200
    past_debt.refresh_from_db()
    current_debt.refresh_from_db()
    assert past_debt.is_deleted is False
    assert current_debt.is_deleted is True


def test_same_branch_same_domain_seller_can_pay_and_cross_domain_seller_cannot(
    api_client,
    users,
    branches,
    debt_factory,
):
    other_phone_seller = models.User.objects.create_user(username="peer_phone_seller", password="pass123")
    models.BranchUser.objects.create(
        user=other_phone_seller,
        branch=branches["main"],
        role=models.BranchUser.ROLE_PHONE_SELLER,
    )
    debt = debt_factory(
        branch=branches["main"],
        created_by=other_phone_seller,
        f_name="Payable Debt",
        remaining_amount=Decimal("100.00"),
        domain=models.Debt.DOMAIN_PHONE,
    )

    api_client.force_authenticate(user=users["phone_seller"])
    allowed = api_client.post(
        reverse("api_debt_pay", args=[debt.id]),
        {"amount": "10.00", "note": "Seller payment"},
        format="json",
    )
    assert allowed.status_code == 200

    api_client.force_authenticate(user=users["accessory_seller"])
    blocked = api_client.post(
        reverse("api_debt_pay", args=[debt.id]),
        {"amount": "10.00", "note": "Wrong domain payment"},
        format="json",
    )
    assert blocked.status_code == 403


def test_payment_delete_only_owner_and_cross_type_visibility_for_payment_list(
    api_client,
    users,
    branches,
    debt_factory,
):
    phone_debt = debt_factory(
        branch=branches["main"],
        created_by=users["phone_seller"],
        domain=models.Debt.DOMAIN_PHONE,
        f_name="Phone Debt",
        remaining_amount=Decimal("50.00"),
    )
    accessory_debt = debt_factory(
        branch=branches["main"],
        created_by=users["accessory_seller"],
        domain=models.Debt.DOMAIN_ACCESSORY,
        f_name="Accessory Debt",
        remaining_amount=Decimal("50.00"),
    )

    api_client.force_authenticate(user=users["owner"])
    phone_payment_resp = api_client.post(
        reverse("api_debt_pay", args=[phone_debt.id]),
        {"amount": "10.00", "note": "Phone payment"},
        format="json",
    )
    assert phone_payment_resp.status_code == 200
    phone_payment_id = phone_payment_resp.json()["data"]["id"]

    accessory_payment_resp = api_client.post(
        reverse("api_debt_pay", args=[accessory_debt.id]),
        {"amount": "10.00", "note": "Accessory payment"},
        format="json",
    )
    assert accessory_payment_resp.status_code == 200

    api_client.force_authenticate(user=users["phone_seller"])
    phone_seller_payments = api_client.get(reverse("api_debt_payment_list"))
    assert phone_seller_payments.status_code == 200
    payment_ids = _result_ids(phone_seller_payments)
    assert phone_payment_id in payment_ids

    api_client.force_authenticate(user=users["accessory_seller"])
    accessory_seller_payments = api_client.get(reverse("api_debt_payment_list"))
    assert accessory_seller_payments.status_code == 200
    payment_ids = _result_ids(accessory_seller_payments)
    assert phone_payment_id not in payment_ids

    api_client.force_authenticate(user=users["phone_seller"])
    blocked_delete = api_client.delete(reverse("api_debt_payment_delete", args=[phone_payment_id]))
    assert blocked_delete.status_code == 403

    api_client.force_authenticate(user=users["owner"])
    allowed_delete = api_client.delete(reverse("api_debt_payment_delete", args=[phone_payment_id]))
    assert allowed_delete.status_code == 200
    assert models.DebtPayment.objects.filter(pk=phone_payment_id, is_deleted=False).exists() is False
