"""User API tests."""

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


def test_superadmin_can_list_users(api_client, users):
    """Superadmin can list paginated users."""
    api_client.force_authenticate(user=users["admin"])

    response = api_client.get(reverse("api_user_list"))

    assert response.status_code == 200
    payload = _paginated_data(response)
    assert payload["count"] >= 6


def test_user_list_filters_work(api_client, users, branches):
    """User list supports safe admin filters."""
    models.BranchUser.objects.create(
        user=users["outsider"],
        branch=branches["other"],
        role=models.BranchUser.ROLE_OWNER,
    )
    users["outsider"].is_active = False
    users["outsider"].save(update_fields=["is_active"])

    api_client.force_authenticate(user=users["admin"])

    role_response = api_client.get(reverse("api_user_list"), {"role": "PHONE_SELLER"})
    role_ids = {item["id"] for item in _paginated_data(role_response)["results"]}
    assert users["phone_seller"].id in role_ids
    assert users["accessory_seller"].id not in role_ids

    branch_response = api_client.get(reverse("api_user_list"), {"branch": branches["other"].id})
    branch_ids = {item["id"] for item in _paginated_data(branch_response)["results"]}
    assert users["outsider"].id in branch_ids
    assert users["phone_seller"].id not in branch_ids

    active_response = api_client.get(reverse("api_user_list"), {"active": "false"})
    active_ids = {item["id"] for item in _paginated_data(active_response)["results"]}
    assert users["outsider"].id in active_ids
    assert users["phone_seller"].id not in active_ids


def test_unauthorized_roles_cannot_access_user_admin_api(api_client, users):
    """Business users cannot access admin user APIs."""
    api_client.force_authenticate(user=users["owner"])

    list_response = api_client.get(reverse("api_user_list"))
    patch_response = api_client.patch(
        reverse("api_user_detail", args=[users["phone_seller"].id]),
        {"first_name": "Blocked"},
        format="json",
    )

    assert list_response.status_code == 403
    assert patch_response.status_code == 403


def test_superadmin_can_view_and_update_user(api_client, users):
    """Superadmin can retrieve and patch users."""
    api_client.force_authenticate(user=users["admin"])

    detail_response = api_client.get(reverse("api_user_detail", args=[users["phone_seller"].id]))
    assert detail_response.status_code == 200
    assert detail_response.json()["data"]["id"] == users["phone_seller"].id

    patch_response = api_client.patch(
        reverse("api_user_detail", args=[users["phone_seller"].id]),
        {
            "first_name": "Updated",
            "daily_fee": "4500.00",
            "is_cashier": True,
        },
        format="json",
    )

    assert patch_response.status_code == 200
    users["phone_seller"].refresh_from_db()
    assert users["phone_seller"].first_name == "Updated"
    assert str(users["phone_seller"].daily_fee) == "4500.00"
    assert users["phone_seller"].is_cashier is True


def test_me_requires_auth(api_client):
    """Current-user profile endpoint requires authentication."""
    response = api_client.get(reverse("api_me"))
    assert response.status_code == 401


def test_me_returns_current_user_data_roles_branches_theme_and_has_pin(api_client, users, branches):
    """Current-user profile returns the authenticated user's mobile context."""
    owner = users["owner"]
    owner.first_name = "Mobile"
    owner.last_name = "Owner"
    owner.phone = "+998900001122"
    owner.theme = models.User.THEME_LIGHT
    owner.set_mobile_pin("1234")
    owner.save()
    api_client.force_authenticate(user=owner)

    response = api_client.get(reverse("api_me"))

    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == owner.id
    assert payload["username"] == owner.username
    assert payload["first_name"] == "Mobile"
    assert payload["last_name"] == "Owner"
    assert payload["full_name"] == "Mobile Owner"
    assert payload["phone"] == "+998900001122"
    assert payload["account_status"] == owner.account_status
    assert payload["is_superuser"] is False
    assert payload["is_cashier"] is False
    assert payload["theme"] == models.User.THEME_LIGHT
    assert payload["has_pin"] is True
    assert payload["pin_enabled"] is True

    roles = {
        (item["branch_id"], item["branch_name"], item["role"])
        for item in payload["roles"]
    }
    assert roles == {
        (branches["main"].id, branches["main"].name, models.BranchUser.ROLE_OWNER),
        (branches["other"].id, branches["other"].name, models.BranchUser.ROLE_OWNER),
    }

    branch_summaries = {
        (item["id"], item["name"], item["role"])
        for item in payload["branches"]
    }
    assert branch_summaries == {
        (branches["main"].id, branches["main"].name, models.BranchUser.ROLE_OWNER),
        (branches["other"].id, branches["other"].name, models.BranchUser.ROLE_OWNER),
    }


def test_me_settings_updates_own_username(api_client, users):
    """Authenticated users can update only their own username."""
    api_client.force_authenticate(user=users["owner"])

    response = api_client.patch(
        reverse("api_me_settings"),
        {"username": "owner_mobile_updated"},
        format="json",
    )

    assert response.status_code == 200
    users["owner"].refresh_from_db()
    users["outsider"].refresh_from_db()
    assert users["owner"].username == "owner_mobile_updated"
    assert users["outsider"].username == "outsider_api"
    assert response.json()["username"] == "owner_mobile_updated"


def test_me_settings_rejects_duplicate_username(api_client, users):
    """Authenticated users cannot claim another user's username."""
    api_client.force_authenticate(user=users["owner"])

    response = api_client.patch(
        reverse("api_me_settings"),
        {"username": users["outsider"].username},
        format="json",
    )

    assert response.status_code == 400
    assert "username" in response.json()


def test_me_settings_updates_theme_and_me_returns_it(api_client, users):
    """Theme updates persist and are returned by /me."""
    api_client.force_authenticate(user=users["owner"])

    patch_response = api_client.patch(
        reverse("api_me_settings"),
        {"theme": models.User.THEME_DARK},
        format="json",
    )

    assert patch_response.status_code == 200
    assert patch_response.json()["theme"] == models.User.THEME_DARK

    users["owner"].refresh_from_db()
    assert users["owner"].theme == models.User.THEME_DARK

    get_response = api_client.get(reverse("api_me"))
    assert get_response.status_code == 200
    assert get_response.json()["theme"] == models.User.THEME_DARK
