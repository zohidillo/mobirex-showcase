from decimal import Decimal

import pytest
from django.urls import reverse

from src.core import models


pytestmark = pytest.mark.django_db


def _paginated_data(response):
    payload = response.json()
    assert payload["success"] is True
    data = payload["data"]
    assert "count" in data
    assert "next" in data
    assert "previous" in data
    assert "results" in data
    assert len(data["results"]) <= 20
    return data


def _result_ids(response):
    return {item["id"] for item in _paginated_data(response)["results"]}


def test_api_owner_can_list_owned_branch_records_with_current_month_default_and_branch_filter(
    api_client,
    users,
    branches,
    extra_profit_factory,
    set_model_datetime,
    time_points,
):
    current_main = extra_profit_factory(
        branch=branches["main"],
        created_by=users["phone_seller"],
        note="Current main",
    )
    previous_main = extra_profit_factory(
        branch=branches["main"],
        created_by=users["phone_seller"],
        note="Previous main",
    )
    current_other_owned = extra_profit_factory(
        branch=branches["other"],
        created_by=users["owner"],
        note="Current other owned",
    )

    other_owner = models.User.objects.create_user(username="other_owner_extra", password="pass123")
    foreign_branch = models.Branch.objects.create(name="Foreign Branch", owner=other_owner)
    models.BranchUser.objects.create(
        user=other_owner,
        branch=foreign_branch,
        role=models.BranchUser.ROLE_OWNER,
    )
    foreign_item = extra_profit_factory(
        branch=foreign_branch,
        created_by=other_owner,
        note="Foreign current",
    )

    set_model_datetime(
        current_main,
        added_at=time_points["current"],
        updated_at=time_points["current"],
    )
    set_model_datetime(
        previous_main,
        added_at=time_points["previous"],
        updated_at=time_points["previous"],
    )
    set_model_datetime(
        current_other_owned,
        added_at=time_points["current"],
        updated_at=time_points["current"],
    )
    set_model_datetime(
        foreign_item,
        added_at=time_points["current"],
        updated_at=time_points["current"],
    )

    api_client.force_authenticate(user=users["owner"])

    default_response = api_client.get(reverse("api_extra_profit_list_create"))
    assert default_response.status_code == 200
    default_ids = _result_ids(default_response)
    assert current_main.id in default_ids
    assert current_other_owned.id in default_ids
    assert previous_main.id not in default_ids
    assert foreign_item.id not in default_ids

    previous_response = api_client.get(
        reverse("api_extra_profit_list_create"),
        {
            "year": str(time_points["previous"].year),
            "month": str(time_points["previous"].month),
        },
    )
    assert previous_response.status_code == 200
    assert _result_ids(previous_response) == {previous_main.id}

    branch_response = api_client.get(
        reverse("api_extra_profit_list_create"),
        {"branch": branches["other"].id},
    )
    assert branch_response.status_code == 200
    assert _result_ids(branch_response) == {current_other_owned.id}


def test_api_owner_cannot_create_extra_profit(api_client, users, branches):
    """Owner cannot create extra profit."""
    api_client.force_authenticate(user=users["owner"])
    response = api_client.post(
        reverse("api_extra_profit_list_create"),
        {
            "branch": branches["main"].id,
            "amount": "30.00",
            "note": "Owner extra profit",
        },
        format="json",
    )
    assert response.status_code == 403
    assert models.ExtraProfit.objects.filter(note="Owner extra profit", is_deleted=False).exists() is False


def test_api_owner_can_delete_current_month_extra_profit_in_owned_branch(
    api_client,
    users,
    branches,
    extra_profit_factory,
    capital_factory,
):
    """Owner can delete current-month extra profit in owned branch."""
    month_start = capital_factory(
        "PhoneCapital",
        branch=branches["main"],
        current_balance=Decimal("200.00"),
        invested_amount=Decimal("200.00"),
    ).month
    phone_capital = models.PhoneCapital.objects.get(branch=branches["main"], month=month_start)

    current_item = extra_profit_factory(
        branch=branches["main"],
        created_by=users["phone_seller"],
        amount=Decimal("30.00"),
        note="Owner deletable item",
    )

    api_client.force_authenticate(user=users["owner"])
    response = api_client.delete(reverse("api_extra_profit_delete", args=[current_item.id]))
    assert response.status_code == 200
    current_item.refresh_from_db()
    assert current_item.is_deleted is True
    phone_capital.refresh_from_db()
    assert phone_capital.current_balance == Decimal("170.00")


def test_api_owner_cannot_delete_extra_profit_in_non_owned_branch(
    api_client,
    users,
    branches,
    extra_profit_factory,
):
    """Owner cannot delete extra profit from a branch they don't own."""
    other_owner = models.User.objects.create_user(username="other_owner_ep", password="pass123")
    other_branch = models.Branch.objects.create(name="Other EP Branch", owner=other_owner)
    models.BranchUser.objects.create(
        user=other_owner,
        branch=other_branch,
        role=models.BranchUser.ROLE_OWNER,
    )
    other_seller = models.User.objects.create_user(username="other_ep_seller", password="pass123")
    models.BranchUser.objects.create(
        user=other_seller,
        branch=other_branch,
        role=models.BranchUser.ROLE_PHONE_SELLER,
    )
    other_item = extra_profit_factory(
        branch=other_branch,
        created_by=other_seller,
        note="Other branch item",
    )

    api_client.force_authenticate(user=users["owner"])
    response = api_client.delete(reverse("api_extra_profit_delete", args=[other_item.id]))
    assert response.status_code == 404
    other_item.refresh_from_db()
    assert other_item.is_deleted is False


def test_api_phone_seller_can_create_extra_profit_for_own_branch_and_phone_capital(
    api_client,
    users,
    branches,
    capital_factory,
):
    month_start = capital_factory(
        "PhoneCapital",
        current_balance=Decimal("100.00"),
        invested_amount=Decimal("100.00"),
    ).month
    phone_capital = models.PhoneCapital.objects.get(branch=branches["main"], month=month_start)
    accessory_capital = capital_factory(
        "AccessoryCapital",
        branch=branches["main"],
        month=month_start,
        current_balance=Decimal("90.00"),
        invested_amount=Decimal("90.00"),
    )

    api_client.force_authenticate(user=users["phone_seller"])
    response = api_client.post(
        reverse("api_extra_profit_list_create"),
        {
            "branch": branches["other"].id,
            "amount": "12.00",
            "note": "Phone seller extra profit",
        },
        format="json",
    )

    assert response.status_code == 201
    extra_profit = models.ExtraProfit.objects.get(note="Phone seller extra profit")
    assert extra_profit.branch_id == branches["main"].id
    assert extra_profit.created_by_id == users["phone_seller"].id

    phone_capital.refresh_from_db()
    accessory_capital.refresh_from_db()
    assert phone_capital.current_balance == Decimal("112.00")
    assert accessory_capital.current_balance == Decimal("90.00")


def test_api_accessory_seller_cannot_create_extra_profit(
    api_client,
    users,
    branches,
    capital_factory,
):
    """Accessory seller is blocked from creating extra profit."""
    capital_factory(
        "AccessoryCapital",
        current_balance=Decimal("100.00"),
        invested_amount=Decimal("100.00"),
    )
    capital_factory(
        "PhoneCapital",
        branch=branches["main"],
        current_balance=Decimal("150.00"),
        invested_amount=Decimal("150.00"),
    )

    api_client.force_authenticate(user=users["accessory_seller"])
    response = api_client.post(
        reverse("api_extra_profit_list_create"),
        {
            "amount": "9.00",
            "note": "Accessory seller extra profit attempt",
        },
        format="json",
    )

    assert response.status_code == 403
    assert models.ExtraProfit.objects.filter(
        note="Accessory seller extra profit attempt", is_deleted=False
    ).exists() is False


def test_api_accessory_seller_cannot_list_extra_profit(api_client, users, branches, extra_profit_factory):
    """Accessory seller is blocked from viewing extra profit list."""
    extra_profit_factory(branch=branches["main"], created_by=users["phone_seller"], note="EP item")

    api_client.force_authenticate(user=users["accessory_seller"])
    response = api_client.get(reverse("api_extra_profit_list_create"))
    assert response.status_code == 403


def test_api_seller_list_and_delete_are_limited_to_own_branch_and_domain(
    api_client,
    users,
    branches,
    extra_profit_factory,
):
    phone_item = extra_profit_factory(
        branch=branches["main"],
        created_by=users["phone_seller"],
        note="Phone domain record",
    )
    accessory_item = extra_profit_factory(
        branch=branches["main"],
        created_by=users["accessory_seller"],
        note="Accessory domain record",
    )
    other_branch_seller = models.User.objects.create_user(username="other_phone_extra", password="pass123")
    models.BranchUser.objects.create(
        user=other_branch_seller,
        branch=branches["other"],
        role=models.BranchUser.ROLE_PHONE_SELLER,
    )
    other_branch_item = extra_profit_factory(
        branch=branches["other"],
        created_by=other_branch_seller,
        note="Other branch phone record",
    )

    api_client.force_authenticate(user=users["phone_seller"])

    list_response = api_client.get(reverse("api_extra_profit_list_create"))
    assert list_response.status_code == 200
    ids = _result_ids(list_response)
    assert phone_item.id in ids
    assert accessory_item.id not in ids
    assert other_branch_item.id not in ids

    # Accessory item not in phone seller's queryset -> 404
    wrong_domain_delete = api_client.delete(reverse("api_extra_profit_delete", args=[accessory_item.id]))
    assert wrong_domain_delete.status_code == 404
    accessory_item.refresh_from_db()
    assert accessory_item.is_deleted is False

    cross_branch_delete = api_client.delete(reverse("api_extra_profit_delete", args=[other_branch_item.id]))
    assert cross_branch_delete.status_code == 404
    other_branch_item.refresh_from_db()
    assert other_branch_item.is_deleted is False


def test_api_phone_seller_can_delete_own_current_month_extra_profit(
    api_client,
    users,
    branches,
    capital_factory,
):
    """Phone seller can delete only their own current-month extra profit."""
    peer_phone_seller = models.User.objects.create_user(username="peer_phone_extra", password="pass123")
    models.BranchUser.objects.create(
        user=peer_phone_seller,
        branch=branches["main"],
        role=models.BranchUser.ROLE_PHONE_SELLER,
    )

    month_start = capital_factory(
        "PhoneCapital",
        branch=branches["main"],
        current_balance=Decimal("100.00"),
        invested_amount=Decimal("100.00"),
    ).month
    accessory_capital = capital_factory(
        "AccessoryCapital",
        branch=branches["main"],
        month=month_start,
        current_balance=Decimal("200.00"),
        invested_amount=Decimal("200.00"),
    )
    other_branch_phone_capital = capital_factory(
        "PhoneCapital",
        branch=branches["other"],
        month=month_start,
        current_balance=Decimal("300.00"),
        invested_amount=Decimal("300.00"),
    )

    # peer_phone_seller creates extra_profit -> phone_capital goes to 125.00
    api_client.force_authenticate(user=peer_phone_seller)
    create_response = api_client.post(
        reverse("api_extra_profit_list_create"),
        {"amount": "25.00", "note": "Peer phone extra"},
        format="json",
    )
    assert create_response.status_code == 201
    extra_profit_id = create_response.json()["data"]["id"]

    phone_capital = models.PhoneCapital.objects.get(branch=branches["main"], month=month_start)
    phone_capital.refresh_from_db()
    assert phone_capital.current_balance == Decimal("125.00")

    # users["phone_seller"] tries to delete peer's item -> 403 (not own item)
    api_client.force_authenticate(user=users["phone_seller"])
    delete_peer = api_client.delete(reverse("api_extra_profit_delete", args=[extra_profit_id]))
    assert delete_peer.status_code == 403

    extra_profit = models.ExtraProfit.all_objects.get(pk=extra_profit_id)
    assert extra_profit.is_deleted is False
    phone_capital.refresh_from_db()
    assert phone_capital.current_balance == Decimal("125.00")

    # peer_phone_seller deletes own item -> 200, capital reversed
    api_client.force_authenticate(user=peer_phone_seller)
    delete_own = api_client.delete(reverse("api_extra_profit_delete", args=[extra_profit_id]))
    assert delete_own.status_code == 200

    extra_profit.refresh_from_db()
    assert extra_profit.is_deleted is True
    phone_capital.refresh_from_db()
    accessory_capital.refresh_from_db()
    other_branch_phone_capital.refresh_from_db()
    assert phone_capital.current_balance == Decimal("100.00")
    assert accessory_capital.current_balance == Decimal("200.00")
    assert other_branch_phone_capital.current_balance == Decimal("300.00")


def test_api_seller_cannot_delete_past_month_extra_profit(
    api_client,
    users,
    branches,
    capital_factory,
    extra_profit_factory,
    set_model_datetime,
    time_points,
):
    month_start = capital_factory(
        "PhoneCapital",
        branch=branches["main"],
        current_balance=Decimal("180.00"),
        invested_amount=Decimal("180.00"),
    ).month
    extra_profit = extra_profit_factory(
        branch=branches["main"],
        created_by=users["phone_seller"],
        amount=Decimal("20.00"),
        note="Past month extra",
    )
    set_model_datetime(
        extra_profit,
        added_at=time_points["previous"],
        updated_at=time_points["previous"],
    )

    api_client.force_authenticate(user=users["phone_seller"])
    delete_response = api_client.delete(reverse("api_extra_profit_delete", args=[extra_profit.id]))
    assert delete_response.status_code == 403

    extra_profit.refresh_from_db()
    assert extra_profit.is_deleted is False
    phone_capital = models.PhoneCapital.objects.get(branch=branches["main"], month=month_start)
    phone_capital.refresh_from_db()
    assert phone_capital.current_balance == Decimal("180.00")


def test_api_delete_subtracts_from_phone_capital_only(
    api_client,
    users,
    branches,
    extra_profit_factory,
    capital_factory,
):
    """Extra profit delete always subtracts from PhoneCapital, never AccessoryCapital."""
    month_start = capital_factory(
        "PhoneCapital",
        branch=branches["main"],
        current_balance=Decimal("500.00"),
        invested_amount=Decimal("500.00"),
    ).month
    accessory_capital = capital_factory(
        "AccessoryCapital",
        branch=branches["main"],
        month=month_start,
        current_balance=Decimal("300.00"),
        invested_amount=Decimal("300.00"),
    )
    phone_capital = models.PhoneCapital.objects.get(branch=branches["main"], month=month_start)

    item = extra_profit_factory(
        branch=branches["main"],
        created_by=users["phone_seller"],
        amount=Decimal("50.00"),
        note="Delete capital test",
    )

    api_client.force_authenticate(user=users["phone_seller"])
    response = api_client.delete(reverse("api_extra_profit_delete", args=[item.id]))
    assert response.status_code == 200

    phone_capital.refresh_from_db()
    accessory_capital.refresh_from_db()
    assert phone_capital.current_balance == Decimal("450.00")
    assert accessory_capital.current_balance == Decimal("300.00")
