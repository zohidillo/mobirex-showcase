"""Demo (app-review) accounts must not mutate their own credentials or delete
themselves. Each restricted endpoint should return 403 with a clear English
message, while non-demo users and non-restricted actions keep working.
"""

import pytest
from django.urls import reverse

from src.core import models
from src.shared.demo import DEMO_ACTION_BLOCKED_MESSAGE


pytestmark = pytest.mark.django_db


@pytest.fixture
def demo_user(db):
    """A seeded-style demo review login (identified purely by username)."""
    return models.User.objects.create_user(username="demo_owner", password="pass123")


@pytest.fixture
def normal_user(db):
    """A regular, non-demo user used to prove the gate is demo-only."""
    return models.User.objects.create_user(username="real_owner_demo", password="pass123")


def _bodies(response):
    """Both response envelopes expose the message; flatten them for assertions."""
    payload = response.json()
    return payload.get("error") or payload.get("detail") or ""


# ---- model flag ----


def test_is_demo_flag_only_true_for_demo_usernames(demo_user, normal_user):
    assert demo_user.is_demo is True
    assert normal_user.is_demo is False


# ---- password change ----


def test_demo_cannot_change_password(api_client, demo_user):
    api_client.force_authenticate(user=demo_user)
    response = api_client.post(
        reverse("api_auth_change_password"),
        {"old_password": "pass123", "new_password": "newpass123", "confirm_password": "newpass123"},
        format="json",
    )
    assert response.status_code == 403
    assert DEMO_ACTION_BLOCKED_MESSAGE in _bodies(response)
    demo_user.refresh_from_db()
    assert demo_user.check_password("pass123")


def test_normal_user_can_still_change_password(api_client, normal_user):
    api_client.force_authenticate(user=normal_user)
    response = api_client.post(
        reverse("api_auth_change_password"),
        {"old_password": "pass123", "new_password": "newpass123", "confirm_password": "newpass123"},
        format="json",
    )
    assert response.status_code == 200


# ---- PIN ----


def test_demo_cannot_set_pin(api_client, demo_user):
    api_client.force_authenticate(user=demo_user)
    response = api_client.post(reverse("api_auth_pin_set"), {"pin": "1234"}, format="json")
    assert response.status_code == 403
    assert DEMO_ACTION_BLOCKED_MESSAGE in _bodies(response)
    demo_user.refresh_from_db()
    assert demo_user.mobile_pin_hash in (None, "")


def test_demo_cannot_change_pin(api_client, demo_user):
    demo_user.set_mobile_pin("1234")
    demo_user.save()
    api_client.force_authenticate(user=demo_user)
    response = api_client.post(
        reverse("api_auth_pin_change"),
        {"old_pin": "1234", "new_pin": "5678"},
        format="json",
    )
    assert response.status_code == 403
    demo_user.refresh_from_db()
    assert demo_user.check_mobile_pin("1234") is True


def test_demo_can_still_verify_pin(api_client, demo_user):
    """Verifying the PIN must keep working so reviewers can log in."""
    demo_user.set_mobile_pin("1234")
    demo_user.save()
    api_client.force_authenticate(user=demo_user)
    response = api_client.post(reverse("api_auth_pin_verify"), {"pin": "1234"}, format="json")
    assert response.status_code == 200
    assert response.json() == {"success": True}


def test_normal_user_can_still_set_pin(api_client, normal_user):
    api_client.force_authenticate(user=normal_user)
    response = api_client.post(reverse("api_auth_pin_set"), {"pin": "1234"}, format="json")
    assert response.status_code == 200


# ---- username change ----


def test_demo_cannot_change_username(api_client, demo_user):
    api_client.force_authenticate(user=demo_user)
    response = api_client.patch(
        reverse("api_me_settings"),
        {"username": "hacked_demo"},
        format="json",
    )
    assert response.status_code == 403
    assert DEMO_ACTION_BLOCKED_MESSAGE in _bodies(response)
    demo_user.refresh_from_db()
    assert demo_user.username == "demo_owner"


def test_demo_can_still_change_theme(api_client, demo_user):
    """Theme-only settings updates are not credential changes; keep them allowed."""
    api_client.force_authenticate(user=demo_user)
    response = api_client.patch(reverse("api_me_settings"), {"theme": "dark"}, format="json")
    assert response.status_code == 200
    demo_user.refresh_from_db()
    assert demo_user.theme == "dark"


def test_demo_same_username_is_not_blocked(api_client, demo_user):
    """Sending the unchanged username must not trip the guard."""
    api_client.force_authenticate(user=demo_user)
    response = api_client.patch(
        reverse("api_me_settings"),
        {"username": "demo_owner", "theme": "light"},
        format="json",
    )
    assert response.status_code == 200


def test_normal_user_can_still_change_username(api_client, normal_user):
    api_client.force_authenticate(user=normal_user)
    response = api_client.patch(
        reverse("api_me_settings"),
        {"username": "renamed_owner_demo"},
        format="json",
    )
    assert response.status_code == 200
    normal_user.refresh_from_db()
    assert normal_user.username == "renamed_owner_demo"


# ---- account deletion (support request) ----


def test_demo_cannot_request_account_deletion(api_client, demo_user):
    demo_user.phone = "+998900000000"
    demo_user.save()
    api_client.force_authenticate(user=demo_user)
    response = api_client.post(
        reverse("api_support_request_list_create"),
        {"request_type": models.SupportRequest.RequestType.ACCOUNT_DELETE},
        format="json",
    )
    assert response.status_code == 403
    assert DEMO_ACTION_BLOCKED_MESSAGE in _bodies(response)
    assert not models.SupportRequest.objects.filter(user=demo_user).exists()


def test_normal_user_can_still_request_account_deletion(api_client, normal_user):
    normal_user.phone = "+998900000001"
    normal_user.save()
    api_client.force_authenticate(user=normal_user)
    response = api_client.post(
        reverse("api_support_request_list_create"),
        {"request_type": models.SupportRequest.RequestType.ACCOUNT_DELETE},
        format="json",
    )
    assert response.status_code == 201
    assert models.SupportRequest.objects.filter(user=normal_user).exists()
