"""Login rejects blocked accounts with a distinguishable structured error."""

from datetime import timedelta
from decimal import Decimal

import pytest
from django.urls import reverse
from django.utils import timezone


pytestmark = pytest.mark.django_db


def test_blocked_login_returns_account_blocked_code(api_client, users):
    """Blocked account login → 401 carrying code=account_blocked + message."""
    owner = users["owner"]
    owner.balance = Decimal("-9900.00")
    owner.grace_start_date = timezone.localdate() - timedelta(days=3)
    owner.save(update_fields=["balance", "grace_start_date"])

    response = api_client.post(
        reverse("api_auth_login"),
        {"username": owner.username, "password": "pass123"},
        format="json",
    )

    assert response.status_code == 401
    payload = response.json()
    assert payload["code"] == "account_blocked"
    assert payload["account_status"] == "blocked"
    assert payload["detail"] != ""


def test_wrong_password_is_not_account_blocked(api_client, users):
    """Wrong credentials stay a plain 401 without the account_blocked code."""
    response = api_client.post(
        reverse("api_auth_login"),
        {"username": users["owner"].username, "password": "wrong-pass"},
        format="json",
    )

    assert response.status_code == 401
    assert response.json().get("code") != "account_blocked"
