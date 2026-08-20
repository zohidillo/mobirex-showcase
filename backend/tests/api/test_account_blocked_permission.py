"""Billing-block enforcement on protected APIs (BaseAPIView → 402)."""

from datetime import timedelta
from decimal import Decimal

import pytest
from django.urls import reverse
from django.utils import timezone


pytestmark = pytest.mark.django_db


def _block(user):
    user.balance = Decimal("-9900.00")
    user.grace_start_date = timezone.localdate() - timedelta(days=3)
    user.save(update_fields=["balance", "grace_start_date"])
    return user


def test_blocked_user_gets_402_on_protected_endpoint(api_client, users, branches):
    """A blocked user hitting a BaseAPIView endpoint gets a structured 402."""
    owner = _block(users["owner"])
    api_client.force_authenticate(user=owner)

    response = api_client.get(reverse("api_me_branches"))

    assert response.status_code == 402
    payload = response.json()
    assert payload["success"] is False
    assert payload["data"] is None
    assert payload["error"]["code"] == "account_blocked"
    assert payload["error"]["account_status"] == "blocked"
    assert payload["error"]["message"] != ""


def test_blocked_user_can_still_read_me(api_client, users, branches):
    """/api/me/ stays 200 for a blocked user so the app can show the reason."""
    owner = _block(users["owner"])
    api_client.force_authenticate(user=owner)

    response = api_client.get(reverse("api_me"))

    assert response.status_code == 200
    assert response.json()["billing"]["is_blocked"] is True


def test_active_user_not_blocked(api_client, users, branches):
    """An active user passes the billing gate normally."""
    api_client.force_authenticate(user=users["owner"])

    response = api_client.get(reverse("api_me_branches"))

    assert response.status_code == 200


def test_vip_user_not_blocked(api_client, users, branches):
    """VIP/demo users are never blocked even with a deep negative balance."""
    owner = _block(users["owner"])
    owner.is_vip = True
    owner.save(update_fields=["is_vip"])
    api_client.force_authenticate(user=owner)

    response = api_client.get(reverse("api_me_branches"))

    assert response.status_code == 200


def test_anonymous_still_gets_401(api_client):
    """Unauthenticated requests keep returning 401, not 402."""
    response = api_client.get(reverse("api_me_branches"))
    assert response.status_code == 401
