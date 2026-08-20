"""Billing payment API tests."""

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


def test_cashier_can_create_payment_and_balance_updates(api_client, users):
    """Cashier can create payments through the billing service."""
    api_client.force_authenticate(user=users["cashier"])

    response = api_client.post(
        reverse("api_billing_payment_list_create"),
        {
            "user": users["phone_seller"].id,
            "amount": "75.00",
            "payment_type": "cash",
        },
        format="json",
    )

    assert response.status_code == 201
    users["phone_seller"].refresh_from_db()
    assert users["phone_seller"].balance == Decimal("75.00")
    assert models.Payment.objects.filter(user=users["phone_seller"], amount=Decimal("75.00")).exists()
    assert models.TransactionLog.objects.filter(
        user=users["phone_seller"],
        type="payment",
        amount=Decimal("75.00"),
    ).exists()


def test_unauthorized_users_cannot_create_payments(api_client, users):
    """Normal business users cannot access cashier payment creation."""
    api_client.force_authenticate(user=users["owner"])

    response = api_client.post(
        reverse("api_billing_payment_list_create"),
        {
            "user": users["phone_seller"].id,
            "amount": "50.00",
            "payment_type": "cash",
        },
        format="json",
    )

    assert response.status_code == 403


def test_payment_list_filters_and_pagination_work(
    api_client,
    users,
    payment_factory,
    set_model_datetime,
    time_points,
):
    """Payment list matches cashier filtering behavior."""
    current_cash = payment_factory(user=users["phone_seller"], amount=Decimal("10.00"), payment_type="cash")
    previous_payme = payment_factory(
        user=users["owner"],
        amount=Decimal("20.00"),
        payment_type="payme",
    )
    for index in range(19):
        payment_factory(amount=Decimal("5.00"), payment_type="cash")

    set_model_datetime(
        current_cash,
        added_at=time_points["current"],
        updated_at=time_points["current"],
    )
    set_model_datetime(
        previous_payme,
        added_at=time_points["previous"],
        updated_at=time_points["previous"],
    )

    api_client.force_authenticate(user=users["cashier"])

    default_response = api_client.get(reverse("api_billing_payment_list_create"))
    default_payload = _paginated_data(default_response)
    assert default_payload["count"] == 21
    assert len(default_payload["results"]) == 20
    assert default_payload["next"] is not None
    assert default_payload["previous"] is None

    filtered_response = api_client.get(
        reverse("api_billing_payment_list_create"),
        {
            "user": users["owner"].id,
            "payment_type": "payme",
            "year": str(time_points["previous"].year),
            "month": str(time_points["previous"].month),
        },
    )
    filtered_payload = _paginated_data(filtered_response)
    assert filtered_payload["count"] == 1
    assert filtered_payload["results"][0]["id"] == previous_payme.id

    page_two_response = api_client.get(
        reverse("api_billing_payment_list_create"),
        {"page": 2},
    )
    page_two_payload = _paginated_data(page_two_response)
    assert page_two_payload["next"] is None
    assert page_two_payload["previous"] is not None
