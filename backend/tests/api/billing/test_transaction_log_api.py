"""Transaction log API tests."""

from datetime import timedelta
from decimal import Decimal

import pytest
from django.urls import reverse


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


def test_user_sees_only_own_transaction_logs(api_client, users, transaction_log_factory):
    """Regular users only see their own transaction logs."""
    own_log = transaction_log_factory(user=users["phone_seller"])
    other_log = transaction_log_factory(user=users["owner"])

    api_client.force_authenticate(user=users["phone_seller"])
    response = api_client.get(reverse("api_billing_transaction_list"))

    assert response.status_code == 200
    result_ids = {item["id"] for item in _paginated_data(response)["results"]}
    assert own_log.id in result_ids
    assert other_log.id not in result_ids


def test_cashier_and_admin_see_all_transaction_logs(api_client, users, transaction_log_factory):
    """Cashier and admin can see all transaction logs."""
    cashier_visible = transaction_log_factory(user=users["phone_seller"])
    admin_visible = transaction_log_factory(user=users["owner"], amount=Decimal("75.00"))

    api_client.force_authenticate(user=users["cashier"])
    cashier_response = api_client.get(reverse("api_billing_transaction_list"))
    cashier_ids = {item["id"] for item in _paginated_data(cashier_response)["results"]}
    assert cashier_visible.id in cashier_ids
    assert admin_visible.id in cashier_ids

    api_client.force_authenticate(user=users["admin"])
    admin_response = api_client.get(reverse("api_billing_transaction_list"))
    admin_ids = {item["id"] for item in _paginated_data(admin_response)["results"]}
    assert cashier_visible.id in admin_ids
    assert admin_visible.id in admin_ids


def test_transaction_log_filters_and_pagination_work(
    api_client,
    users,
    transaction_log_factory,
    set_model_datetime,
    time_points,
):
    """Transaction log filters match the live billing pages."""
    current_log = transaction_log_factory(
        user=users["phone_seller"],
        type="payment",
        amount=Decimal("10.00"),
    )
    previous_log = transaction_log_factory(
        user=users["owner"],
        type="daily_charge",
        amount=Decimal("20.00"),
    )

    set_model_datetime(
        current_log,
        charge_date=time_points["current"] + timedelta(hours=1),
        charge_day=(time_points["current"] + timedelta(hours=1)).date(),
        updated_at=time_points["current"] + timedelta(hours=1),
    )
    set_model_datetime(
        previous_log,
        charge_date=time_points["previous"],
        charge_day=time_points["previous"].date(),
        updated_at=time_points["previous"],
    )

    for index in range(19):
        transaction_log_factory(
            user=users["phone_seller"],
            amount=Decimal("5.00"),
            type="payment",
        )

    api_client.force_authenticate(user=users["cashier"])

    default_response = api_client.get(reverse("api_billing_transaction_list"))
    default_payload = _paginated_data(default_response)
    assert default_payload["count"] == 21
    assert len(default_payload["results"]) == 20
    assert default_payload["next"] is not None
    assert default_payload["previous"] is None

    filtered_response = api_client.get(
        reverse("api_billing_transaction_list"),
        {
            "user": users["owner"].id,
            "transaction_type": "daily_charge",
            "year": str(time_points["previous"].year),
            "month": str(time_points["previous"].month),
        },
    )
    filtered_payload = _paginated_data(filtered_response)
    assert filtered_payload["count"] == 1
    assert filtered_payload["results"][0]["id"] == previous_log.id

    page_two_response = api_client.get(reverse("api_billing_transaction_list"), {"page": 2})
    page_two_payload = _paginated_data(page_two_response)
    assert page_two_payload["next"] is None
    assert page_two_payload["previous"] is not None
