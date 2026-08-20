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


def _create_user(username):
    return models.User.objects.create_user(username=username, password="pass123")


def _assign_role(user, branch, role):
    return models.BranchUser.objects.create(user=user, branch=branch, role=role)


def test_unsold_list_accessory_seller_only_own_branch(api_client, users, branches, accessory_factory):
    own_accessory = accessory_factory(name="Own Accessory")
    other_accessory = accessory_factory(name="Other Accessory", branch=branches["other"])

    api_client.force_authenticate(user=users["accessory_seller"])
    response = api_client.get(reverse("api_accessory_unsold_list"))

    assert response.status_code == 200
    ids = _result_ids(response)
    assert own_accessory.id in ids
    assert other_accessory.id not in ids


def test_sold_list_accessory_seller_only_own_branch(api_client, users, branches, accessory_factory):
    own_accessory = accessory_factory(name="Own Sold Accessory", stock=5)
    other_accessory = accessory_factory(
        name="Other Sold Accessory",
        branch=branches["other"],
        stock=5,
    )

    api_client.force_authenticate(user=users["accessory_seller"])
    own_sale_response = api_client.post(
        reverse("api_accessory_sell", args=[own_accessory.id]),
        {"quantity": 1, "total_price": "20.00"},
        format="json",
    )
    assert own_sale_response.status_code == 200
    own_sale_id = own_sale_response.json()["data"]["id"]

    other_seller = _create_user("other_branch_accessory_seller")
    _assign_role(other_seller, branches["other"], models.BranchUser.ROLE_ACCESSORY_SELLER)
    api_client.force_authenticate(user=other_seller)
    other_sale_response = api_client.post(
        reverse("api_accessory_sell", args=[other_accessory.id]),
        {"quantity": 1, "total_price": "25.00"},
        format="json",
    )
    assert other_sale_response.status_code == 200

    api_client.force_authenticate(user=users["accessory_seller"])
    sold_response = api_client.get(reverse("api_accessory_sold_list"))
    assert sold_response.status_code == 200
    ids = _result_ids(sold_response)
    assert own_sale_id in ids
    assert other_sale_response.json()["data"]["id"] not in ids


def test_phone_seller_denied_accessory_lists(api_client, users):
    api_client.force_authenticate(user=users["phone_seller"])

    unsold_response = api_client.get(reverse("api_accessory_unsold_list"))
    assert unsold_response.status_code == 403

    sold_response = api_client.get(reverse("api_accessory_sold_list"))
    assert sold_response.status_code == 403


def test_other_branch_owner_cannot_see_main_branch_accessories(api_client, users, branches, accessory_factory):
    main_accessory = accessory_factory(name="Main Branch Accessory")

    other_owner = _create_user("other_owner")
    other_branch = models.Branch.objects.create(name="Other Owner Branch", owner=other_owner)
    _assign_role(other_owner, other_branch, models.BranchUser.ROLE_OWNER)
    accessory_factory(name="Other Owner Accessory", branch=other_branch)

    api_client.force_authenticate(user=other_owner)
    response = api_client.get(reverse("api_accessory_unsold_list"))
    assert response.status_code == 200
    ids = _result_ids(response)
    assert main_accessory.id not in ids


def test_owner_sees_own_branches_accessories(api_client, users, accessory_factory):
    accessory = accessory_factory(name="Owner Accessory")
    api_client.force_authenticate(user=users["owner"])

    response = api_client.get(reverse("api_accessory_unsold_list"))
    assert response.status_code == 200
    assert accessory.id in _result_ids(response)


def test_owner_branch_filter_works(api_client, users, branches, accessory_factory):
    _assign_role(users["owner"], branches["other"], models.BranchUser.ROLE_OWNER)

    main_accessory = accessory_factory(name="Main Filter Accessory", branch=branches["main"])
    other_accessory = accessory_factory(name="Other Filter Accessory", branch=branches["other"])

    api_client.force_authenticate(user=users["owner"])

    response = api_client.get(reverse("api_accessory_unsold_list"))
    assert response.status_code == 200
    ids = _result_ids(response)
    assert main_accessory.id in ids
    assert other_accessory.id in ids

    main_response = api_client.get(
        reverse("api_accessory_unsold_list"),
        {"branch": branches["main"].id},
    )
    assert main_response.status_code == 200
    assert _result_ids(main_response) == {main_accessory.id}

    other_response = api_client.get(
        reverse("api_accessory_unsold_list"),
        {"branch": branches["other"].id},
    )
    assert other_response.status_code == 200
    assert _result_ids(other_response) == {other_accessory.id}


def test_owner_employee_filter_works(api_client, users, branches, accessory_factory):
    other_seller = _create_user("second_accessory_seller")
    _assign_role(other_seller, branches["main"], models.BranchUser.ROLE_ACCESSORY_SELLER)

    by_first = accessory_factory(name="By First Seller", added_by=users["accessory_seller"])
    by_second = accessory_factory(name="By Second Seller", added_by=other_seller)

    api_client.force_authenticate(user=users["owner"])
    response = api_client.get(
        reverse("api_accessory_unsold_list"),
        {"employee": users["accessory_seller"].id},
    )
    assert response.status_code == 200
    assert _result_ids(response) == {by_first.id}
    assert by_second.id not in _result_ids(response)


def test_unsold_filters_search_and_category_work(api_client, users, branches, categories, accessory_factory):
    other_category = models.AccessoryCategory.objects.create(name="Chargers")

    case = accessory_factory(
        name="Silicone Case",
        category=categories["accessory"],
        branch=branches["main"],
    )
    charger = accessory_factory(
        name="Fast Charger",
        category=other_category,
        branch=branches["main"],
    )

    api_client.force_authenticate(user=users["accessory_seller"])

    search_response = api_client.get(reverse("api_accessory_unsold_list"), {"q": "Silicone"})
    assert search_response.status_code == 200
    assert _result_ids(search_response) == {case.id}

    category_response = api_client.get(
        reverse("api_accessory_unsold_list"),
        {"category": other_category.id},
    )
    assert category_response.status_code == 200
    assert _result_ids(category_response) == {charger.id}


def test_sold_filters_search_category_year_month_work(
    api_client,
    users,
    branches,
    categories,
    accessory_factory,
    set_model_datetime,
    time_points,
):
    other_category = models.AccessoryCategory.objects.create(name="Chargers")
    case = accessory_factory(name="Silicone Case", category=categories["accessory"], stock=10)
    charger = accessory_factory(name="Fast Charger", category=other_category, stock=10)

    api_client.force_authenticate(user=users["accessory_seller"])
    sale_case_response = api_client.post(
        reverse("api_accessory_sell", args=[case.id]),
        {"quantity": 1, "total_price": "15.00"},
        format="json",
    )
    sale_charger_response = api_client.post(
        reverse("api_accessory_sell", args=[charger.id]),
        {"quantity": 1, "total_price": "25.00"},
        format="json",
    )
    assert sale_case_response.status_code == 200
    assert sale_charger_response.status_code == 200

    sale_case = models.AccessorySale.objects.get(pk=sale_case_response.json()["data"]["id"])
    sale_charger = models.AccessorySale.objects.get(pk=sale_charger_response.json()["data"]["id"])

    set_model_datetime(sale_case, sold_at=time_points["previous"])

    default_response = api_client.get(reverse("api_accessory_sold_list"))
    assert default_response.status_code == 200
    assert _result_ids(default_response) == {sale_charger.id}

    search_response = api_client.get(reverse("api_accessory_sold_list"), {"q": "Fast"})
    assert search_response.status_code == 200
    assert _result_ids(search_response) == {sale_charger.id}

    category_response = api_client.get(
        reverse("api_accessory_sold_list"),
        {"category": other_category.id},
    )
    assert category_response.status_code == 200
    assert _result_ids(category_response) == {sale_charger.id}

    previous_response = api_client.get(
        reverse("api_accessory_sold_list"),
        {
            "year": str(time_points["previous"].year),
            "month": str(time_points["previous"].month),
        },
    )
    assert previous_response.status_code == 200
    assert _result_ids(previous_response) == {sale_case.id}


def test_add_accessory_permissions(api_client, users, branches, categories):
    api_client.force_authenticate(user=users["phone_seller"])
    denied_response = api_client.post(
        reverse("api_accessory_create"),
        {
            "branch": branches["main"].id,
            "name": "Denied Accessory",
            "category": categories["accessory"].id,
            "stock": 2,
            "unit_cost": "10.00",
        },
        format="json",
    )
    assert denied_response.status_code == 403

    api_client.force_authenticate(user=users["accessory_seller"])
    seller_response = api_client.post(
        reverse("api_accessory_create"),
        {
            "branch": branches["other"].id,
            "name": "Seller Accessory",
            "category": categories["accessory"].id,
            "stock": 2,
            "unit_cost": "10.00",
        },
        format="json",
    )
    assert seller_response.status_code == 201
    accessory = models.Accessory.objects.get(pk=seller_response.json()["data"]["id"])
    assert accessory.branch_id == branches["main"].id

    api_client.force_authenticate(user=users["owner"])
    owner_response = api_client.post(
        reverse("api_accessory_create"),
        {
            "branch": branches["main"].id,
            "name": "Owner Accessory",
            "category": categories["accessory"].id,
            "stock": 3,
            "unit_cost": "12.00",
        },
        format="json",
    )
    assert owner_response.status_code == 201
    assert models.Accessory.objects.get(pk=owner_response.json()["data"]["id"]).branch_id == branches[
        "main"
    ].id


def test_sell_accessory_permissions_and_stock_validation(api_client, users, accessory_factory):
    accessory = accessory_factory(name="Sellable", stock=2)

    api_client.force_authenticate(user=users["phone_seller"])
    denied_response = api_client.post(
        reverse("api_accessory_sell", args=[accessory.id]),
        {"quantity": 1, "total_price": "20.00"},
        format="json",
    )
    assert denied_response.status_code == 403

    api_client.force_authenticate(user=users["accessory_seller"])
    invalid_response = api_client.post(
        reverse("api_accessory_sell", args=[accessory.id]),
        {"quantity": 5, "total_price": "100.00"},
        format="json",
    )
    assert invalid_response.status_code == 400
    assert "quantity" in invalid_response.json()["error"]

    ok_response = api_client.post(
        reverse("api_accessory_sell", args=[accessory.id]),
        {"quantity": 1, "total_price": "20.00"},
        format="json",
    )
    assert ok_response.status_code == 200
    accessory.refresh_from_db()
    assert accessory.stock == 1


def test_return_current_month_sold_accessory_works(api_client, users, accessory_factory):
    accessory = accessory_factory(name="Returnable", stock=5)
    api_client.force_authenticate(user=users["accessory_seller"])

    sell_response = api_client.post(
        reverse("api_accessory_sell", args=[accessory.id]),
        {"quantity": 2, "total_price": "50.00"},
        format="json",
    )
    assert sell_response.status_code == 200
    sale_id = sell_response.json()["data"]["id"]

    return_response = api_client.post(reverse("api_accessory_return", args=[sale_id]), format="json")
    assert return_response.status_code == 200

    accessory.refresh_from_db()
    assert accessory.stock == 5
    assert models.AccessorySale.all_objects.get(pk=sale_id).is_deleted is True


def test_return_previous_month_sold_accessory_fails(
    api_client,
    users,
    accessory_factory,
    set_model_datetime,
    time_points,
):
    accessory = accessory_factory(name="Past Sale", stock=5)
    api_client.force_authenticate(user=users["accessory_seller"])

    sell_response = api_client.post(
        reverse("api_accessory_sell", args=[accessory.id]),
        {"quantity": 1, "total_price": "20.00"},
        format="json",
    )
    assert sell_response.status_code == 200
    sale_id = sell_response.json()["data"]["id"]

    sale = models.AccessorySale.objects.get(pk=sale_id)
    set_model_datetime(sale, sold_at=time_points["previous"])

    return_response = api_client.post(reverse("api_accessory_return", args=[sale_id]), format="json")
    assert return_response.status_code == 400
    assert "Oldingi oy" in return_response.json()["error"]

    accessory.refresh_from_db()
    assert accessory.stock == 4
    sale.refresh_from_db()
    assert sale.is_deleted is False


def test_delete_accessory_permissions(api_client, users, branches, accessory_factory):
    by_seller = accessory_factory(name="Seller Added", added_by=users["accessory_seller"])
    by_owner = accessory_factory(name="Owner Added", added_by=users["owner"])

    other_seller = _create_user("other_branch_seller")
    _assign_role(other_seller, branches["other"], models.BranchUser.ROLE_ACCESSORY_SELLER)

    api_client.force_authenticate(user=users["phone_seller"])
    assert (
        api_client.delete(reverse("api_accessory_delete", args=[by_owner.id])).status_code == 403
    )

    api_client.force_authenticate(user=users["accessory_seller"])
    assert (
        api_client.delete(reverse("api_accessory_delete", args=[by_owner.id])).status_code == 403
    )
    ok_delete = api_client.delete(reverse("api_accessory_delete", args=[by_seller.id]))
    assert ok_delete.status_code == 200
    assert models.Accessory.all_objects.get(pk=by_seller.id).is_deleted is True

    api_client.force_authenticate(user=users["owner"])
    owner_delete = api_client.delete(reverse("api_accessory_delete", args=[by_owner.id]))
    assert owner_delete.status_code == 200
    assert models.Accessory.all_objects.get(pk=by_owner.id).is_deleted is True

    cross_accessory = accessory_factory(name="Cross Branch", added_by=users["owner"])
    api_client.force_authenticate(user=other_seller)
    assert (
        api_client.delete(reverse("api_accessory_delete", args=[cross_accessory.id])).status_code
        == 403
    )


def test_employees_endpoint_owner_only(api_client, users, branches):
    api_client.force_authenticate(user=users["owner"])
    assert api_client.get(reverse("api_accessory_employee_list")).status_code == 200

    api_client.force_authenticate(user=users["accessory_seller"])
    assert api_client.get(reverse("api_accessory_employee_list")).status_code == 403

    api_client.force_authenticate(user=users["phone_seller"])
    assert api_client.get(reverse("api_accessory_employee_list")).status_code == 403


def test_employees_endpoint_role_and_branch_filters_work(api_client, users, branches):
    _assign_role(users["owner"], branches["other"], models.BranchUser.ROLE_OWNER)

    other_accessory_seller = _create_user("other_branch_accessory_seller")
    _assign_role(other_accessory_seller, branches["other"], models.BranchUser.ROLE_ACCESSORY_SELLER)

    api_client.force_authenticate(user=users["owner"])
    main_accessory_sellers = api_client.get(
        reverse("api_accessory_employee_list"),
        {"role": models.BranchUser.ROLE_ACCESSORY_SELLER, "branch": branches["main"].id},
    )
    assert main_accessory_sellers.status_code == 200
    main_ids = {item["id"] for item in main_accessory_sellers.json()["data"]}
    assert users["accessory_seller"].id in main_ids
    assert other_accessory_seller.id not in main_ids

    other_accessory_sellers = api_client.get(
        reverse("api_accessory_employee_list"),
        {"role": models.BranchUser.ROLE_ACCESSORY_SELLER, "branch": branches["other"].id},
    )
    assert other_accessory_sellers.status_code == 200
    other_ids = {item["id"] for item in other_accessory_sellers.json()["data"]}
    assert other_accessory_seller.id in other_ids
    assert users["accessory_seller"].id not in other_ids

    phone_sellers = api_client.get(
        reverse("api_accessory_employee_list"),
        {"role": models.BranchUser.ROLE_PHONE_SELLER, "branch": branches["main"].id},
    )
    assert phone_sellers.status_code == 200
    phone_ids = {item["id"] for item in phone_sellers.json()["data"]}
    assert users["phone_seller"].id in phone_ids


# ---------------------------------------------------------------------------
# Delete / return safety guards
# ---------------------------------------------------------------------------

def _current_month_start():
    from django.utils import timezone
    return timezone.localdate().replace(day=1)


def test_api_delete_blocked_when_active_sale_exists(api_client, users, accessory_factory):
    accessory = accessory_factory(
        name="Has Sale", stock=10, unit_cost=Decimal("10.00"), added_by=users["accessory_seller"]
    )
    api_client.force_authenticate(user=users["accessory_seller"])

    sell_resp = api_client.post(
        reverse("api_accessory_sell", args=[accessory.id]),
        {"quantity": 3, "total_price": "45.00"},
        format="json",
    )
    assert sell_resp.status_code == 200

    # Attempt delete while 3 sales are still active
    delete_resp = api_client.delete(reverse("api_accessory_delete", args=[accessory.id]))
    assert delete_resp.status_code == 400
    assert models.Accessory.all_objects.get(pk=accessory.id).is_deleted is False


def test_api_delete_allowed_after_all_sales_returned(api_client, users, accessory_factory):
    accessory = accessory_factory(
        name="Sale Then Return", stock=5, unit_cost=Decimal("10.00"), added_by=users["accessory_seller"]
    )
    api_client.force_authenticate(user=users["accessory_seller"])

    sell_resp = api_client.post(
        reverse("api_accessory_sell", args=[accessory.id]),
        {"quantity": 2, "total_price": "30.00"},
        format="json",
    )
    assert sell_resp.status_code == 200
    sale_id = sell_resp.json()["data"]["id"]

    return_resp = api_client.post(reverse("api_accessory_return", args=[sale_id]), format="json")
    assert return_resp.status_code == 200

    delete_resp = api_client.delete(reverse("api_accessory_delete", args=[accessory.id]))
    assert delete_resp.status_code == 200
    assert models.Accessory.all_objects.get(pk=accessory.id).is_deleted is True


def test_api_return_blocked_for_soft_deleted_accessory(api_client, users, accessory_factory):
    accessory = accessory_factory(name="To Be Deleted", stock=5, added_by=users["accessory_seller"])
    api_client.force_authenticate(user=users["accessory_seller"])

    sell_resp = api_client.post(
        reverse("api_accessory_sell", args=[accessory.id]),
        {"quantity": 1, "total_price": "15.00"},
        format="json",
    )
    assert sell_resp.status_code == 200
    sale_id = sell_resp.json()["data"]["id"]

    # Force-delete the accessory directly (bypassing service guard)
    models.Accessory.all_objects.filter(pk=accessory.id).update(is_deleted=True)

    return_resp = api_client.post(reverse("api_accessory_return", args=[sale_id]), format="json")
    assert return_resp.status_code == 400
    assert models.AccessorySale.objects.filter(pk=sale_id, is_deleted=False).exists()


def test_api_delete_rolls_back_invested_amount_not_current_balance(
    api_client, users, branches, accessory_factory
):
    month_start = _current_month_start()
    acc_capital = models.AccessoryCapital.objects.create(
        branch=branches["main"],
        month=month_start,
        invested_amount=Decimal("100.00"),
        current_balance=Decimal("200.00"),
    )
    phone_capital = models.PhoneCapital.objects.create(
        branch=branches["main"],
        month=month_start,
        invested_amount=Decimal("0"),
        current_balance=Decimal("500.00"),
    )

    # unit_cost=10, stock=5 → remaining_value = 50
    accessory = accessory_factory(
        name="Capital Check", stock=5, unit_cost=Decimal("10.00"), added_by=users["accessory_seller"]
    )
    api_client.force_authenticate(user=users["accessory_seller"])

    delete_resp = api_client.delete(reverse("api_accessory_delete", args=[accessory.id]))
    assert delete_resp.status_code == 200

    acc_capital.refresh_from_db()
    phone_capital.refresh_from_db()

    assert acc_capital.invested_amount == Decimal("50.00")   # 100 - 50
    assert acc_capital.current_balance == Decimal("200.00")  # unchanged
    assert phone_capital.invested_amount == Decimal("0")     # untouched
    assert phone_capital.current_balance == Decimal("500.00")  # untouched


def test_api_sell_increases_accessory_capital_not_phone_capital(
    api_client, users, branches, accessory_factory
):
    month_start = _current_month_start()
    acc_capital = models.AccessoryCapital.objects.create(
        branch=branches["main"],
        month=month_start,
        invested_amount=Decimal("0"),
        current_balance=Decimal("0"),
    )
    phone_capital = models.PhoneCapital.objects.create(
        branch=branches["main"],
        month=month_start,
        invested_amount=Decimal("0"),
        current_balance=Decimal("1000.00"),
    )

    accessory = accessory_factory(name="Sell Capital", stock=5)
    api_client.force_authenticate(user=users["accessory_seller"])

    sell_resp = api_client.post(
        reverse("api_accessory_sell", args=[accessory.id]),
        {"quantity": 2, "total_price": "40.00"},
        format="json",
    )
    assert sell_resp.status_code == 200

    acc_capital.refresh_from_db()
    phone_capital.refresh_from_db()

    assert acc_capital.current_balance == Decimal("40.00")    # increased by sale total_price
    assert phone_capital.current_balance == Decimal("1000.00")  # untouched


def test_api_return_restores_stock_and_subtracts_accessory_capital(
    api_client, users, branches, accessory_factory
):
    month_start = _current_month_start()
    acc_capital = models.AccessoryCapital.objects.create(
        branch=branches["main"],
        month=month_start,
        invested_amount=Decimal("0"),
        current_balance=Decimal("100.00"),
    )
    phone_capital = models.PhoneCapital.objects.create(
        branch=branches["main"],
        month=month_start,
        invested_amount=Decimal("0"),
        current_balance=Decimal("500.00"),
    )

    accessory = accessory_factory(name="Return Capital", stock=5)
    api_client.force_authenticate(user=users["accessory_seller"])

    sell_resp = api_client.post(
        reverse("api_accessory_sell", args=[accessory.id]),
        {"quantity": 2, "total_price": "30.00"},
        format="json",
    )
    assert sell_resp.status_code == 200
    sale_id = sell_resp.json()["data"]["id"]

    # After sell, acc_capital.current_balance += 30 → 130; phone_capital unchanged
    acc_capital.refresh_from_db()
    assert acc_capital.current_balance == Decimal("130.00")

    return_resp = api_client.post(reverse("api_accessory_return", args=[sale_id]), format="json")
    assert return_resp.status_code == 200

    acc_capital.refresh_from_db()
    phone_capital.refresh_from_db()
    accessory.refresh_from_db()

    assert accessory.stock == 5                               # restored
    assert acc_capital.current_balance == Decimal("100.00")  # 130 - 30
    assert phone_capital.current_balance == Decimal("500.00")  # untouched


def test_api_same_branch_seller_can_sell_peer_added_accessory(
    api_client, users, branches, categories
):
    # Owner adds an accessory in main branch
    peer_seller = _create_user("peer_seller")
    _assign_role(peer_seller, branches["main"], models.BranchUser.ROLE_ACCESSORY_SELLER)

    accessory = models.Accessory.objects.create(
        name="Peer Product",
        category=categories["accessory"],
        branch=branches["main"],
        unit_cost=Decimal("5.00"),
        stock=10,
        added_by=users["owner"],
    )

    # Different seller in same branch can sell it
    api_client.force_authenticate(user=peer_seller)
    sell_resp = api_client.post(
        reverse("api_accessory_sell", args=[accessory.id]),
        {"quantity": 1, "total_price": "10.00"},
        format="json",
    )
    assert sell_resp.status_code == 200
    accessory.refresh_from_db()
    assert accessory.stock == 9


def test_api_seller_cannot_affect_other_branch_accessory_capital(
    api_client, users, branches, categories
):
    month_start = _current_month_start()
    acc_capital_a = models.AccessoryCapital.objects.create(
        branch=branches["main"],
        month=month_start,
        invested_amount=Decimal("0"),
        current_balance=Decimal("0"),
    )
    acc_capital_b = models.AccessoryCapital.objects.create(
        branch=branches["other"],
        month=month_start,
        invested_amount=Decimal("0"),
        current_balance=Decimal("500.00"),
    )

    accessory = models.Accessory.objects.create(
        name="Branch A Accessory",
        category=categories["accessory"],
        branch=branches["main"],
        unit_cost=Decimal("5.00"),
        stock=10,
        added_by=users["owner"],
    )

    api_client.force_authenticate(user=users["accessory_seller"])
    sell_resp = api_client.post(
        reverse("api_accessory_sell", args=[accessory.id]),
        {"quantity": 1, "total_price": "20.00"},
        format="json",
    )
    assert sell_resp.status_code == 200

    acc_capital_a.refresh_from_db()
    acc_capital_b.refresh_from_db()

    assert acc_capital_a.current_balance == Decimal("20.00")   # increased
    assert acc_capital_b.current_balance == Decimal("500.00")  # untouched


def test_api_phone_seller_cannot_delete_accessory(api_client, users, accessory_factory):
    accessory = accessory_factory(name="Phone Cannot Delete")
    api_client.force_authenticate(user=users["phone_seller"])
    resp = api_client.delete(reverse("api_accessory_delete", args=[accessory.id]))
    assert resp.status_code == 403
    assert models.Accessory.all_objects.get(pk=accessory.id).is_deleted is False


def test_api_phone_seller_cannot_sell_accessory(api_client, users, accessory_factory):
    accessory = accessory_factory(name="Phone Cannot Sell", stock=5)
    api_client.force_authenticate(user=users["phone_seller"])
    resp = api_client.post(
        reverse("api_accessory_sell", args=[accessory.id]),
        {"quantity": 1, "total_price": "15.00"},
        format="json",
    )
    assert resp.status_code == 403
