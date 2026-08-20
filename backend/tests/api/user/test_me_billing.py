"""/api/me/ billing exposure tests (display layer only)."""

from datetime import timedelta
from decimal import Decimal

import pytest
from django.urls import reverse
from django.utils import timezone

from src.services.billing import AccountAccessService


pytestmark = pytest.mark.django_db


def _me(api_client, user):
    api_client.force_authenticate(user=user)
    response = api_client.get(reverse("api_me"))
    assert response.status_code == 200
    return response.json()


def test_me_exposes_billing_fields_for_active_user(api_client, users):
    """Active user gets billing block with empty messages and no grace info."""
    payload = _me(api_client, users["owner"])

    assert "balance" in payload
    assert payload["is_vip"] is False
    assert payload["account_status"] == "active"
    assert payload["account_status_display"] == "Faol"

    billing = payload["billing"]
    assert billing["status"] == "active"
    assert billing["is_blocked"] is False
    assert billing["is_grace"] is False
    assert billing["warning_message"] == ""
    assert billing["blocked_message"] == ""
    assert billing["grace_start_date"] is None
    assert billing["grace_days_left"] is None


def test_me_billing_grace_reports_message_and_days_left(api_client, users):
    """Grace user gets warning_message and a positive grace_days_left."""
    user = users["owner"]
    user.balance = Decimal("-9900.00")
    user.grace_start_date = timezone.localdate()
    user.save(update_fields=["balance", "grace_start_date"])

    billing = _me(api_client, user)["billing"]

    assert billing["status"] == "grace"
    assert billing["is_grace"] is True
    assert billing["is_blocked"] is False
    assert "3 kun" in billing["warning_message"]
    assert billing["grace_days_left"] == 3
    assert billing["grace_start_date"] == timezone.localdate().isoformat()


def test_me_billing_blocked_reports_blocked_message(api_client, users):
    """Blocked user gets a blocked_message and no grace_days_left."""
    user = users["owner"]
    user.balance = Decimal("-9900.00")
    user.grace_start_date = timezone.localdate() - timedelta(days=3)
    user.save(update_fields=["balance", "grace_start_date"])
    # Mirror production: the daily-charge job / web middleware persist the
    # raw account_status; /api/me/ itself stays read-only (persist=False).
    AccountAccessService.evaluate_user(user, persist=True)

    payload = _me(api_client, user)
    billing = payload["billing"]

    assert billing["status"] == "blocked"
    assert billing["is_blocked"] is True
    assert billing["is_grace"] is False
    assert billing["blocked_message"] != ""
    assert billing["grace_days_left"] is None
    assert payload["account_status_display"] == "Bloklangan"


def test_me_billing_vip_never_warns(api_client, users):
    """VIP (incl. demo) user is active-allowed: no warnings, no block."""
    user = users["owner"]
    user.is_vip = True
    user.balance = Decimal("-50000.00")
    user.save(update_fields=["is_vip", "balance"])

    payload = _me(api_client, user)
    billing = payload["billing"]

    assert payload["is_vip"] is True
    assert billing["status"] == "vip"
    assert billing["is_blocked"] is False
    assert billing["is_grace"] is False
    assert billing["warning_message"] == ""
    assert billing["blocked_message"] == ""


def test_me_still_returns_existing_fields(api_client, users, branches):
    """Contract guard: new fields are additive, old fields remain intact."""
    payload = _me(api_client, users["owner"])

    for field in (
        "id",
        "username",
        "first_name",
        "last_name",
        "full_name",
        "phone",
        "account_status",
        "is_superuser",
        "is_cashier",
        "theme",
        "has_pin",
        "pin_enabled",
        "roles",
        "branches",
    ):
        assert field in payload
