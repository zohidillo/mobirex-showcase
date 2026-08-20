from decimal import Decimal

import pytest
from django.urls import reverse

from src.core import models


pytestmark = pytest.mark.django_db


def _result_ids(response):
    payload = response.json()
    data = payload.get("data") if isinstance(payload, dict) else None
    if isinstance(data, dict) and "results" in data:
        results = data["results"]
    else:
        results = payload.get("results", [])
    return {item["id"] for item in results}


def test_phone_sold_list_filters_by_sold_month(api_client, users, phone_factory, time_points):
    current_phone = phone_factory(
        imei="VISIBILITY-CURRENT-001",
        is_sold=True,
        sold_at=time_points["current"],
        sold_by=users["phone_seller"],
        sell_price=Decimal("900.00"),
    )
    previous_phone = phone_factory(
        imei="VISIBILITY-PREVIOUS-001",
        is_sold=True,
        sold_at=time_points["previous"],
        sold_by=users["phone_seller"],
        sell_price=Decimal("850.00"),
    )

    api_client.force_authenticate(user=users["phone_seller"])

    current_response = api_client.get(reverse("api_phone_sold_list"))
    previous_response = api_client.get(
        reverse("api_phone_sold_list"),
        {
            "year": str(time_points["previous"].year),
            "month": str(time_points["previous"].month),
        },
    )

    assert current_response.status_code == 200
    assert previous_response.status_code == 200
    assert _result_ids(current_response) == {current_phone.id}
    assert _result_ids(previous_response) == {previous_phone.id}


def test_phone_unsold_previous_month_stays_visible(api_client, users, phone_factory, set_model_datetime, time_points):
    phone = phone_factory(imei="UNSOLD-VISIBILITY-001")
    set_model_datetime(
        phone,
        added_at=time_points["previous"],
        updated_at=time_points["previous"],
    )

    api_client.force_authenticate(user=users["phone_seller"])
    response = api_client.get(reverse("api_phone_unsold_list"))

    assert response.status_code == 200
    assert phone.id in _result_ids(response)


def test_accessory_sold_list_filters_by_sold_month(
    api_client,
    users,
    accessory_factory,
    set_model_datetime,
    time_points,
):
    current_accessory = accessory_factory(name="Accessory Current", stock=10, unit_cost=Decimal("10.00"))
    previous_accessory = accessory_factory(
        name="Accessory Previous",
        stock=10,
        unit_cost=Decimal("12.00"),
    )

    current_sale = models.AccessorySale.objects.create(
        accessory=current_accessory,
        branch=current_accessory.branch,
        quantity=1,
        unit_cost=Decimal("10.00"),
        total_cost=Decimal("10.00"),
        total_price=Decimal("20.00"),
        profit=Decimal("10.00"),
        sold_by=users["accessory_seller"],
        sold_at=time_points["current"],
    )
    previous_sale = models.AccessorySale.objects.create(
        accessory=previous_accessory,
        branch=previous_accessory.branch,
        quantity=1,
        unit_cost=Decimal("12.00"),
        total_cost=Decimal("12.00"),
        total_price=Decimal("24.00"),
        profit=Decimal("12.00"),
        sold_by=users["accessory_seller"],
        sold_at=time_points["current"],
    )
    set_model_datetime(previous_sale, sold_at=time_points["previous"])

    api_client.force_authenticate(user=users["accessory_seller"])

    current_response = api_client.get(reverse("api_accessory_sold_list"))
    previous_response = api_client.get(
        reverse("api_accessory_sold_list"),
        {
            "year": str(time_points["previous"].year),
            "month": str(time_points["previous"].month),
        },
    )

    assert current_response.status_code == 200
    assert previous_response.status_code == 200
    assert _result_ids(current_response) == {current_sale.id}
    assert _result_ids(previous_response) == {previous_sale.id}


def test_accessory_unsold_previous_month_stays_visible(
    api_client,
    users,
    accessory_factory,
    set_model_datetime,
    time_points,
):
    accessory = accessory_factory(name="Accessory Previous Stock", stock=4)
    set_model_datetime(
        accessory,
        added_at=time_points["previous"],
        updated_at=time_points["previous"],
    )

    api_client.force_authenticate(user=users["accessory_seller"])
    response = api_client.get(reverse("api_accessory_unsold_list"))

    assert response.status_code == 200
    assert accessory.id in _result_ids(response)


def test_debt_list_stays_in_created_month(api_client, users, debt_factory, set_model_datetime, time_points):
    current_debt = debt_factory(
        f_name="Debt Current Visibility",
        created_by=users["owner"],
        domain=models.Debt.DOMAIN_PHONE,
    )
    previous_debt = debt_factory(
        f_name="Debt Previous Visibility",
        created_by=users["owner"],
        domain=models.Debt.DOMAIN_PHONE,
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

    api_client.force_authenticate(user=users["owner"])

    current_response = api_client.get(reverse("api_debt_list_create"))
    previous_response = api_client.get(
        reverse("api_debt_list_create"),
        {
            "year": str(time_points["previous"].year),
            "month": str(time_points["previous"].month),
        },
    )

    assert current_response.status_code == 200
    assert previous_response.status_code == 200
    assert _result_ids(current_response) == {current_debt.id}
    assert _result_ids(previous_response) == {previous_debt.id}


def test_expense_list_stays_in_created_month(api_client, users, expense_factory, set_model_datetime, time_points):
    current_expense = expense_factory(note="Expense Current Visibility", created_by=users["owner"])
    previous_expense = expense_factory(note="Expense Previous Visibility", created_by=users["owner"])
    set_model_datetime(
        current_expense,
        added_at=time_points["current"],
        updated_at=time_points["current"],
    )
    set_model_datetime(
        previous_expense,
        added_at=time_points["previous"],
        updated_at=time_points["previous"],
    )

    api_client.force_authenticate(user=users["owner"])

    current_response = api_client.get(reverse("api_expense_list_create"))
    previous_response = api_client.get(
        reverse("api_expense_list_create"),
        {
            "year": str(time_points["previous"].year),
            "month": str(time_points["previous"].month),
        },
    )

    assert current_response.status_code == 200
    assert previous_response.status_code == 200
    assert _result_ids(current_response) == {current_expense.id}
    assert _result_ids(previous_response) == {previous_expense.id}
