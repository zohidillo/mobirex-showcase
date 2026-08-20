from decimal import Decimal

import pytest
from django.test import Client
from django.urls import reverse
from django.utils import timezone

from src.core import models
from src.services.phone import PhoneCreateService, PhoneService


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


def _phone_create_payload(branch, category, imei, *, cost_price="500.00"):
    return {
        "branch": branch,
        "name": "Phone Model",
        "category": category,
        "storage": "128",
        "color": "Black",
        "from_by": "Supplier",
        "imei": imei,
        "cost_price": Decimal(str(cost_price)),
    }


def test_create_phone_works_for_seller(api_client, users, branches, categories):
    api_client.force_authenticate(user=users["phone_seller"])

    response = api_client.post(
        reverse("api_phone_create"),
        {
            "branch": branches["other"].id,
            "name": "iPhone 16",
            "category": categories["phone"].id,
            "storage": "256",
            "color": "Blue",
            "from_by": "Supplier",
            "imei": "PHONE-SELLER-001",
            "cost_price": "800.00",
        },
        format="json",
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["success"] is True

    phone = models.Phone.objects.get(imei="PHONE-SELLER-001")
    assert phone.branch_id == branches["main"].id
    assert phone.added_by_id == users["phone_seller"].id


def test_owner_sees_own_branch_phones(api_client, users, phone_factory):
    phone = phone_factory(imei="PHONE-OWNER-SEE-001")
    api_client.force_authenticate(user=users["owner"])

    response = api_client.get(reverse("api_phone_unsold_list"))

    assert response.status_code == 200
    assert phone.id in _result_ids(response)


def test_owner_cannot_see_other_owner_branch_phones(api_client, users, phone_factory):
    other_owner = models.User.objects.create_user(username="other_owner", password="pass123")
    other_branch = models.Branch.objects.create(name="Other Owner Branch", owner=other_owner)
    models.BranchUser.objects.create(
        user=other_owner,
        branch=other_branch,
        role=models.BranchUser.ROLE_OWNER,
    )
    other_phone = phone_factory(imei="PHONE-OTHER-OWNER-001", branch=other_branch)

    api_client.force_authenticate(user=users["owner"])
    response = api_client.get(reverse("api_phone_unsold_list"))

    assert response.status_code == 200
    assert other_phone.id not in _result_ids(response)


def test_phone_seller_sees_only_own_branch_phones(api_client, users, phone_factory, branches):
    own_phone = phone_factory(imei="PHONE-SELLER-OWN-001")
    other_phone = phone_factory(imei="PHONE-SELLER-OTHER-001", branch=branches["other"])

    api_client.force_authenticate(user=users["phone_seller"])
    response = api_client.get(reverse("api_phone_unsold_list"))

    assert response.status_code == 200
    ids = _result_ids(response)
    assert own_phone.id in ids
    assert other_phone.id not in ids


def test_accessory_seller_denied(api_client, users):
    api_client.force_authenticate(user=users["accessory_seller"])
    assert api_client.get(reverse("api_phone_unsold_list")).status_code == 403
    assert api_client.get(reverse("api_phone_sold_list")).status_code == 403


def test_cashier_denied(api_client, users):
    api_client.force_authenticate(user=users["cashier"])
    assert api_client.get(reverse("api_phone_unsold_list")).status_code == 403
    assert api_client.get(reverse("api_phone_sold_list")).status_code == 403


def test_unsold_filters_work(api_client, users, phone_factory, categories):
    other_category = models.PhoneCategory.objects.create(name="Feature Phones")

    phone_a = phone_factory(
        imei="FILTER-UNSOLD-001",
        name="iPhone Alpha",
        storage="128",
        category=categories["phone"],
    )
    phone_b = phone_factory(
        imei="FILTER-UNSOLD-002",
        name="Samsung Beta",
        storage="256",
        category=categories["phone"],
    )
    phone_c = phone_factory(
        imei="FILTER-UNSOLD-003",
        name="iPhone Gamma",
        storage="256",
        category=other_category,
    )

    api_client.force_authenticate(user=users["phone_seller"])

    by_name = api_client.get(reverse("api_phone_unsold_list"), {"q": "iPhone"})
    assert by_name.status_code == 200
    ids = _result_ids(by_name)
    assert phone_a.id in ids
    assert phone_c.id in ids
    assert phone_b.id not in ids

    by_imei = api_client.get(reverse("api_phone_unsold_list"), {"q": "FILTER-UNSOLD-002"})
    assert by_imei.status_code == 200
    ids = _result_ids(by_imei)
    assert phone_b.id in ids
    assert phone_a.id not in ids

    by_storage = api_client.get(reverse("api_phone_unsold_list"), {"storage": "256"})
    assert by_storage.status_code == 200
    ids = _result_ids(by_storage)
    assert phone_b.id in ids
    assert phone_c.id in ids
    assert phone_a.id not in ids

    by_category = api_client.get(reverse("api_phone_unsold_list"), {"category": other_category.id})
    assert by_category.status_code == 200
    ids = _result_ids(by_category)
    assert phone_c.id in ids
    assert phone_a.id not in ids
    assert phone_b.id not in ids


def test_sold_filters_work(api_client, users, phone_factory, categories, time_points):
    other_category = models.PhoneCategory.objects.create(name="Other Sold Category")

    sold_current_a = phone_factory(
        imei="FILTER-SOLD-CUR-001",
        name="iPhone Sold Alpha",
        storage="128",
        category=categories["phone"],
        is_sold=True,
        sold_at=time_points["current"],
        sold_by=users["phone_seller"],
        sell_price=Decimal("900.00"),
    )
    sold_current_b = phone_factory(
        imei="FILTER-SOLD-CUR-002",
        name="Samsung Sold Beta",
        storage="256",
        category=other_category,
        is_sold=True,
        sold_at=time_points["current"],
        sold_by=users["phone_seller"],
        sell_price=Decimal("800.00"),
    )
    sold_previous = phone_factory(
        imei="FILTER-SOLD-PREV-001",
        name="Old Sold Phone",
        storage="128",
        category=categories["phone"],
        is_sold=True,
        sold_at=time_points["previous"],
        sold_by=users["phone_seller"],
        sell_price=Decimal("700.00"),
    )

    api_client.force_authenticate(user=users["phone_seller"])

    default_response = api_client.get(reverse("api_phone_sold_list"))
    assert default_response.status_code == 200
    ids = _result_ids(default_response)
    assert sold_current_a.id in ids
    assert sold_current_b.id in ids
    assert sold_previous.id not in ids

    prev_filter = api_client.get(
        reverse("api_phone_sold_list"),
        {"year": str(time_points["previous"].year), "month": str(time_points["previous"].month)},
    )
    assert prev_filter.status_code == 200
    ids = _result_ids(prev_filter)
    assert sold_previous.id in ids
    assert sold_current_a.id not in ids
    assert sold_current_b.id not in ids

    by_name = api_client.get(reverse("api_phone_sold_list"), {"q": "Samsung"})
    assert by_name.status_code == 200
    ids = _result_ids(by_name)
    assert sold_current_b.id in ids
    assert sold_current_a.id not in ids

    by_imei = api_client.get(reverse("api_phone_sold_list"), {"q": "FILTER-SOLD-CUR-001"})
    assert by_imei.status_code == 200
    ids = _result_ids(by_imei)
    assert sold_current_a.id in ids
    assert sold_current_b.id not in ids

    by_storage = api_client.get(reverse("api_phone_sold_list"), {"storage": "256"})
    assert by_storage.status_code == 200
    ids = _result_ids(by_storage)
    assert sold_current_b.id in ids
    assert sold_current_a.id not in ids

    by_category = api_client.get(reverse("api_phone_sold_list"), {"category": other_category.id})
    assert by_category.status_code == 200
    ids = _result_ids(by_category)
    assert sold_current_b.id in ids
    assert sold_current_a.id not in ids


def test_owner_can_delete_allowed_phone(api_client, users, phone_factory):
    phone = phone_factory(imei="PHONE-DEL-OWNER-001")
    api_client.force_authenticate(user=users["owner"])

    response = api_client.delete(reverse("api_phone_delete", args=[phone.id]))

    assert response.status_code == 200
    phone.refresh_from_db()
    assert phone.is_deleted is True


def test_same_branch_phone_seller_can_delete_allowed_phone(api_client, users, phone_factory):
    phone = phone_factory(imei="PHONE-DEL-SELLER-001", added_by=users["phone_seller"])
    api_client.force_authenticate(user=users["phone_seller"])

    response = api_client.delete(reverse("api_phone_delete", args=[phone.id]))

    assert response.status_code == 200
    phone.refresh_from_db()
    assert phone.is_deleted is True


def test_other_branch_phone_seller_cannot_delete(api_client, users, phone_factory, branches):
    phone = phone_factory(imei="PHONE-DEL-OTHER-001", branch=branches["other"], added_by=users["phone_seller"])
    api_client.force_authenticate(user=users["phone_seller"])

    response = api_client.delete(reverse("api_phone_delete", args=[phone.id]))

    assert response.status_code == 403


def test_accessory_seller_cannot_delete(api_client, users, phone_factory):
    phone = phone_factory(imei="PHONE-DEL-ACC-001")
    api_client.force_authenticate(user=users["accessory_seller"])
    assert api_client.delete(reverse("api_phone_delete", args=[phone.id])).status_code == 403


def test_cashier_cannot_delete(api_client, users, phone_factory):
    phone = phone_factory(imei="PHONE-DEL-CASH-001")
    api_client.force_authenticate(user=users["cashier"])
    assert api_client.delete(reverse("api_phone_delete", args=[phone.id])).status_code == 403


def test_api_sold_phone_must_be_returned_before_delete(api_client, users, branches, categories, capital_factory):
    capital = capital_factory(
        "PhoneCapital",
        branch=branches["main"],
        invested_amount=Decimal("1000.00"),
        current_balance=Decimal("1000.00"),
    )
    phone = PhoneCreateService.create_phone(
        _phone_create_payload(
            branches["main"],
            categories["phone"],
            "PHONE-DEL-SOLD-API-001",
            cost_price="200.00",
        ),
        added_by=users["phone_seller"],
    )
    capital.refresh_from_db()
    assert capital.current_balance == Decimal("800.00")
    assert capital.invested_amount == Decimal("1000.00")

    PhoneService.sell_phone(phone, sell_price=Decimal("300.00"), sold_by=users["phone_seller"])
    capital.refresh_from_db()
    assert capital.current_balance == Decimal("1100.00")
    assert capital.invested_amount == Decimal("1000.00")

    api_client.force_authenticate(user=users["phone_seller"])

    delete_response = api_client.delete(reverse("api_phone_delete", args=[phone.id]))

    assert delete_response.status_code == 400
    phone.refresh_from_db()
    capital.refresh_from_db()
    assert phone.is_deleted is False
    assert phone.is_sold is True
    assert capital.current_balance == Decimal("1100.00")
    assert capital.invested_amount == Decimal("1000.00")

    return_response = api_client.post(
        reverse("api_phone_return", args=[phone.id]),
        {},
        format="json",
    )
    assert return_response.status_code == 200
    phone.refresh_from_db()
    capital.refresh_from_db()
    assert phone.is_sold is False
    assert capital.current_balance == Decimal("800.00")
    assert capital.invested_amount == Decimal("1000.00")

    delete_after_return = api_client.delete(reverse("api_phone_delete", args=[phone.id]))

    assert delete_after_return.status_code == 200
    phone.refresh_from_db()
    capital.refresh_from_db()
    assert phone.is_deleted is True
    assert capital.current_balance == Decimal("1000.00")
    assert capital.invested_amount == Decimal("1000.00")


def test_api_unsold_delete_restores_cost_price_only_on_own_branch_capital(
    api_client,
    users,
    branches,
    categories,
    capital_factory,
):
    main_capital = capital_factory(
        "PhoneCapital",
        branch=branches["main"],
        invested_amount=Decimal("700.00"),
        current_balance=Decimal("1000.00"),
    )
    other_capital = capital_factory(
        "PhoneCapital",
        branch=branches["other"],
        invested_amount=Decimal("400.00"),
        current_balance=Decimal("650.00"),
    )
    phone = PhoneCreateService.create_phone(
        _phone_create_payload(
            branches["main"],
            categories["phone"],
            "PHONE-DEL-UNSOLD-API-001",
            cost_price="200.00",
        ),
        added_by=users["phone_seller"],
    )

    main_capital.refresh_from_db()
    other_capital.refresh_from_db()
    assert main_capital.current_balance == Decimal("800.00")
    assert other_capital.current_balance == Decimal("650.00")

    api_client.force_authenticate(user=users["phone_seller"])
    response = api_client.delete(reverse("api_phone_delete", args=[phone.id]))

    assert response.status_code == 200
    phone.refresh_from_db()
    main_capital.refresh_from_db()
    other_capital.refresh_from_db()
    assert phone.is_deleted is True
    assert main_capital.current_balance == Decimal("1000.00")
    assert main_capital.invested_amount == Decimal("700.00")
    assert other_capital.current_balance == Decimal("650.00")
    assert other_capital.invested_amount == Decimal("400.00")


def test_sell_works_only_once(api_client, users, phone_factory):
    phone = phone_factory(imei="PHONE-SELL-ONCE-001")
    api_client.force_authenticate(user=users["phone_seller"])

    first = api_client.post(
        reverse("api_phone_sell", args=[phone.id]),
        {"sell_price": "950.00"},
        format="json",
    )
    assert first.status_code == 200

    second = api_client.post(
        reverse("api_phone_sell", args=[phone.id]),
        {"sell_price": "990.00"},
        format="json",
    )
    assert second.status_code == 400


def test_return_current_month_sold_phone_works(api_client, users, phone_factory):
    phone = phone_factory(imei="PHONE-RETURN-CUR-001")
    api_client.force_authenticate(user=users["phone_seller"])

    sell_response = api_client.post(
        reverse("api_phone_sell", args=[phone.id]),
        {"sell_price": "900.00"},
        format="json",
    )
    assert sell_response.status_code == 200

    return_response = api_client.post(
        reverse("api_phone_return", args=[phone.id]),
        {},
        format="json",
    )
    assert return_response.status_code == 200
    payload = return_response.json()
    assert payload["success"] is True
    assert payload["data"]["is_sold"] is False


def test_return_previous_month_sold_phone_fails(api_client, users, phone_factory, time_points):
    phone = phone_factory(
        imei="PHONE-RETURN-PREV-001",
        is_sold=True,
        sold_at=time_points["previous"],
        sold_by=users["phone_seller"],
        sell_price=Decimal("700.00"),
    )
    api_client.force_authenticate(user=users["phone_seller"])

    response = api_client.post(
        reverse("api_phone_return", args=[phone.id]),
        {},
        format="json",
    )
    assert response.status_code == 400


def test_phone_capital_lifecycle_keeps_invested_amount_unchanged(
    users,
    branches,
    categories,
    capital_factory,
):
    capital = capital_factory(
        "PhoneCapital",
        branch=branches["main"],
        invested_amount=Decimal("900.00"),
        current_balance=Decimal("1000.00"),
    )

    phone = PhoneCreateService.create_phone(
        _phone_create_payload(
            branches["main"],
            categories["phone"],
            "PHONE-CAPITAL-LIFECYCLE-001",
            cost_price="250.00",
        ),
        added_by=users["phone_seller"],
    )
    capital.refresh_from_db()
    assert capital.current_balance == Decimal("750.00")
    assert capital.invested_amount == Decimal("900.00")

    PhoneService.sell_phone(phone, sell_price=Decimal("400.00"), sold_by=users["phone_seller"])
    capital.refresh_from_db()
    assert capital.current_balance == Decimal("1150.00")
    assert capital.invested_amount == Decimal("900.00")

    PhoneService.return_phone(phone, returned_by=users["phone_seller"])
    capital.refresh_from_db()
    assert capital.current_balance == Decimal("750.00")
    assert capital.invested_amount == Decimal("900.00")

    PhoneService.delete_phone(phone, deleted_by=users["phone_seller"])
    capital.refresh_from_db()
    assert capital.current_balance == Decimal("1000.00")
    assert capital.invested_amount == Decimal("900.00")


def test_same_branch_phone_seller_can_see_and_sell_peer_added_phone(
    api_client,
    users,
    branches,
    phone_factory,
):
    peer_phone_seller = models.User.objects.create_user(
        username="peer_phone_seller_api",
        password="pass123",
    )
    models.BranchUser.objects.create(
        user=peer_phone_seller,
        branch=branches["main"],
        role=models.BranchUser.ROLE_PHONE_SELLER,
    )
    phone = phone_factory(
        imei="PHONE-PEER-SELL-001",
        added_by=peer_phone_seller,
    )

    api_client.force_authenticate(user=users["phone_seller"])

    list_response = api_client.get(reverse("api_phone_unsold_list"))
    assert list_response.status_code == 200
    assert phone.id in _result_ids(list_response)

    sell_response = api_client.post(
        reverse("api_phone_sell", args=[phone.id]),
        {"sell_price": "920.00"},
        format="json",
    )
    assert sell_response.status_code == 200
    phone.refresh_from_db()
    assert phone.is_sold is True
    assert phone.sold_by_id == users["phone_seller"].id


def test_accessory_seller_blocked_from_phone_create_sell_return_delete(
    api_client,
    users,
    branches,
    categories,
    phone_factory,
):
    sold_phone = phone_factory(
        imei="PHONE-ACC-BLOCK-RETURN-001",
        is_sold=True,
        sold_at=timezone.now(),
        sold_by=users["phone_seller"],
        sell_price=Decimal("810.00"),
    )
    unsold_phone = phone_factory(imei="PHONE-ACC-BLOCK-DEL-001")

    api_client.force_authenticate(user=users["accessory_seller"])

    create_response = api_client.post(
        reverse("api_phone_create"),
        {
            "branch": branches["main"].id,
            "name": "Accessory Seller Phone",
            "category": categories["phone"].id,
            "storage": "128",
            "color": "Black",
            "from_by": "Supplier",
            "imei": "PHONE-ACC-BLOCK-CREATE-001",
            "cost_price": "500.00",
        },
        format="json",
    )
    sell_response = api_client.post(
        reverse("api_phone_sell", args=[unsold_phone.id]),
        {"sell_price": "900.00"},
        format="json",
    )
    return_response = api_client.post(
        reverse("api_phone_return", args=[sold_phone.id]),
        {},
        format="json",
    )
    delete_response = api_client.delete(reverse("api_phone_delete", args=[unsold_phone.id]))

    assert create_response.status_code == 403
    assert sell_response.status_code == 403
    assert return_response.status_code == 403
    assert delete_response.status_code == 403


def test_web_phone_return_flow_still_works(client: Client, users, phone_factory):
    phone = phone_factory(imei="PHONE-WEB-RETURN-001")
    PhoneService.sell_phone(phone, sell_price=Decimal("800.00"), sold_by=users["phone_seller"])

    client.force_login(users["phone_seller"])
    response = client.get(reverse("phone_return", args=[phone.id]))

    assert response.status_code == 302
    assert response.url == reverse("phone_sold_list")

    phone.refresh_from_db()
    assert phone.is_sold is False
    assert phone.sold_at is None
    assert phone.sell_price is None


def test_web_cannot_delete_sold_phone(client: Client, users, branches, categories, capital_factory):
    capital = capital_factory(
        "PhoneCapital",
        branch=branches["main"],
        invested_amount=Decimal("1000.00"),
        current_balance=Decimal("1000.00"),
    )
    phone = PhoneCreateService.create_phone(
        _phone_create_payload(
            branches["main"],
            categories["phone"],
            "PHONE-WEB-SOLD-DELETE-001",
            cost_price="200.00",
        ),
        added_by=users["phone_seller"],
    )
    PhoneService.sell_phone(phone, sell_price=Decimal("300.00"), sold_by=users["phone_seller"])

    client.force_login(users["phone_seller"])
    response = client.post(reverse("phone_delete", args=[phone.id]))

    assert response.status_code == 302
    assert response.url == reverse("phone_unsold_list")
    phone.refresh_from_db()
    capital.refresh_from_db()
    assert phone.is_deleted is False
    assert phone.is_sold is True
    assert capital.current_balance == Decimal("1100.00")
    assert capital.invested_amount == Decimal("1000.00")


def test_web_unsold_delete_restores_cost_price_to_phone_capital(
    client: Client,
    users,
    branches,
    categories,
    capital_factory,
):
    capital = capital_factory(
        "PhoneCapital",
        branch=branches["main"],
        invested_amount=Decimal("800.00"),
        current_balance=Decimal("900.00"),
    )
    phone = PhoneCreateService.create_phone(
        _phone_create_payload(
            branches["main"],
            categories["phone"],
            "PHONE-WEB-UNSOLD-DELETE-001",
            cost_price="200.00",
        ),
        added_by=users["phone_seller"],
    )

    capital.refresh_from_db()
    assert capital.current_balance == Decimal("700.00")

    client.force_login(users["phone_seller"])
    response = client.post(reverse("phone_delete", args=[phone.id]))

    assert response.status_code == 302
    assert response.url == reverse("phone_unsold_list")
    phone.refresh_from_db()
    capital.refresh_from_db()
    assert phone.is_deleted is True
    assert capital.current_balance == Decimal("900.00")
    assert capital.invested_amount == Decimal("800.00")


def test_web_multi_branch_owner_can_delete_phone_from_second_owned_branch(
    client: Client,
    users,
    branches,
    categories,
    capital_factory,
):
    models.BranchUser.objects.create(
        user=users["owner"],
        branch=branches["other"],
        role=models.BranchUser.ROLE_OWNER,
    )
    capital = capital_factory(
        "PhoneCapital",
        branch=branches["other"],
        invested_amount=Decimal("600.00"),
        current_balance=Decimal("600.00"),
    )
    phone = PhoneCreateService.create_phone(
        _phone_create_payload(
            branches["other"],
            categories["phone"],
            "PHONE-WEB-MULTI-OWNER-001",
            cost_price="180.00",
        ),
        added_by=users["owner"],
    )

    capital.refresh_from_db()
    assert capital.current_balance == Decimal("420.00")

    client.force_login(users["owner"])
    response = client.post(reverse("phone_delete", args=[phone.id]))

    assert response.status_code == 302
    assert response.url == reverse("phone_unsold_list")
    phone.refresh_from_db()
    capital.refresh_from_db()
    assert phone.is_deleted is True
    assert capital.current_balance == Decimal("600.00")
