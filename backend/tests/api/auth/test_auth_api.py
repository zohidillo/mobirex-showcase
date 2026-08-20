"""Auth API tests."""

import pytest
from django.urls import reverse


pytestmark = pytest.mark.django_db


def test_login_returns_only_tokens_and_token_authenticates(api_client, users):
    """JWT login returns only access/refresh and can access protected APIs."""
    response = api_client.post(
        reverse("api_auth_login"),
        {
            "username": users["admin"].username,
            "password": "pass123",
        },
        format="json",
    )

    assert response.status_code == 200
    payload = response.json()
    assert set(payload.keys()) == {"access", "refresh"}
    assert "user" not in payload
    assert payload["access"]
    assert payload["refresh"]

    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {payload['access']}")
    protected = api_client.get(reverse("api_user_list"))
    assert protected.status_code == 200


def test_refresh_returns_simplejwt_access_token(api_client, users):
    """Refresh endpoint follows the standard SimpleJWT response shape."""
    login = api_client.post(
        reverse("api_auth_login"),
        {
            "username": users["admin"].username,
            "password": "pass123",
        },
        format="json",
    )

    response = api_client.post(
        reverse("token_refresh"),
        {"refresh": login.json()["refresh"]},
        format="json",
    )

    assert response.status_code == 200
    payload = response.json()
    assert "access" in payload
    assert payload["access"]


def test_invalid_login_fails(api_client, users):
    """Invalid credentials are rejected."""
    response = api_client.post(
        reverse("api_auth_login"),
        {
            "username": users["admin"].username,
            "password": "wrong-pass",
        },
        format="json",
    )

    assert response.status_code == 401
    assert "access" not in response.json()


def test_password_change_works(api_client, users):
    """Authenticated users can change their own password."""
    login = api_client.post(
        reverse("api_auth_login"),
        {
            "username": users["phone_seller"].username,
            "password": "pass123",
        },
        format="json",
    )
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.json()['access']}")

    response = api_client.post(
        reverse("api_auth_change_password"),
        {
            "old_password": "pass123",
            "new_password": "newpass123",
            "confirm_password": "newpass123",
        },
        format="json",
    )

    assert response.status_code == 200
    users["phone_seller"].refresh_from_db()
    assert users["phone_seller"].check_password("newpass123")

    old_login = api_client.post(
        reverse("api_auth_login"),
        {
            "username": users["phone_seller"].username,
            "password": "pass123",
        },
        format="json",
    )
    new_login = api_client.post(
        reverse("api_auth_login"),
        {
            "username": users["phone_seller"].username,
            "password": "newpass123",
        },
        format="json",
    )
    assert old_login.status_code == 401
    assert new_login.status_code == 200


def test_wrong_old_password_fails(api_client, users):
    """Password change rejects an invalid current password."""
    login = api_client.post(
        reverse("api_auth_login"),
        {
            "username": users["owner"].username,
            "password": "pass123",
        },
        format="json",
    )
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.json()['access']}")

    response = api_client.post(
        reverse("api_auth_change_password"),
        {
            "old_password": "wrong-old",
            "new_password": "newpass123",
            "confirm_password": "newpass123",
        },
        format="json",
    )

    assert response.status_code == 400
    assert response.json()["success"] is False


def test_set_pin_accepts_exactly_four_digits(api_client, users):
    """Authenticated users can set a valid 4-digit PIN."""
    api_client.force_authenticate(user=users["owner"])

    response = api_client.post(
        reverse("api_auth_pin_set"),
        {"pin": "1234"},
        format="json",
    )

    assert response.status_code == 200
    assert response.json() == {"success": True, "has_pin": True}


@pytest.mark.parametrize("pin", ["123", "12345", "12ab", "abcd"])
def test_set_pin_rejects_non_digits_and_wrong_length(api_client, users, pin):
    """PIN setup rejects invalid values."""
    api_client.force_authenticate(user=users["owner"])

    response = api_client.post(
        reverse("api_auth_pin_set"),
        {"pin": pin},
        format="json",
    )

    assert response.status_code == 400
    assert "pin" in response.json()


def test_pin_is_stored_hashed_not_plain(api_client, users):
    """PIN hashes are stored securely instead of plaintext."""
    api_client.force_authenticate(user=users["owner"])

    response = api_client.post(
        reverse("api_auth_pin_set"),
        {"pin": "1234"},
        format="json",
    )

    assert response.status_code == 200
    users["owner"].refresh_from_db()
    assert users["owner"].mobile_pin_hash
    assert users["owner"].mobile_pin_hash != "1234"
    assert users["owner"].check_mobile_pin("1234") is True


def test_verify_pin_succeeds_for_correct_pin(api_client, users):
    """PIN verification succeeds when the correct PIN is submitted."""
    users["owner"].set_mobile_pin("1234")
    users["owner"].save()
    api_client.force_authenticate(user=users["owner"])

    response = api_client.post(
        reverse("api_auth_pin_verify"),
        {"pin": "1234"},
        format="json",
    )

    assert response.status_code == 200
    assert response.json() == {"success": True}


def test_verify_pin_fails_for_wrong_pin(api_client, users):
    """PIN verification rejects an incorrect PIN."""
    users["owner"].set_mobile_pin("1234")
    users["owner"].save()
    api_client.force_authenticate(user=users["owner"])

    response = api_client.post(
        reverse("api_auth_pin_verify"),
        {"pin": "5678"},
        format="json",
    )

    assert response.status_code == 400
    assert "pin" in response.json()


def test_change_pin_requires_old_pin_and_stores_new_hash(api_client, users):
    """Changing a PIN requires the old value and replaces the stored hash."""
    users["owner"].set_mobile_pin("1234")
    users["owner"].save()
    old_hash = users["owner"].mobile_pin_hash
    api_client.force_authenticate(user=users["owner"])

    response = api_client.post(
        reverse("api_auth_pin_change"),
        {
            "old_pin": "1234",
            "new_pin": "5678",
        },
        format="json",
    )

    assert response.status_code == 200
    assert response.json() == {"success": True, "has_pin": True}

    users["owner"].refresh_from_db()
    assert users["owner"].mobile_pin_hash != old_hash
    assert users["owner"].check_mobile_pin("1234") is False
    assert users["owner"].check_mobile_pin("5678") is True
