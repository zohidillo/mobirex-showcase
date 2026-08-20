"""Tests for owner mobile helper APIs: /api/me/branches/ and /api/me/staff/."""

import pytest
from django.urls import reverse

from src.core import models


pytestmark = pytest.mark.django_db


def _create_user(username):
    return models.User.objects.create_user(username=username, password="pass123")


def _assign_role(user, branch, role):
    return models.BranchUser.objects.create(user=user, branch=branch, role=role)


# ---- /api/me/branches/ ----


def test_me_branches_returns_owned_branches(api_client, users, branches):
    """Owner branches endpoint returns only branches the user owns."""
    api_client.force_authenticate(user=users["owner"])
    response = api_client.get(reverse("api_me_branches"))
    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    ids = {b["id"] for b in payload["data"]}
    assert branches["main"].id in ids


def test_me_branches_does_not_return_non_owned_branches(api_client, users, branches):
    """Owner branches endpoint does not include branches owned by others."""
    other_owner = _create_user("other_owner_me")
    other_branch = models.Branch.objects.create(name="Other Owner Branch me", owner=other_owner)
    _assign_role(other_owner, other_branch, models.BranchUser.ROLE_OWNER)

    api_client.force_authenticate(user=users["owner"])
    response = api_client.get(reverse("api_me_branches"))
    assert response.status_code == 200
    ids = {b["id"] for b in response.json()["data"]}
    assert other_branch.id not in ids


def test_me_branches_blocked_for_non_owner(api_client, users):
    """Non-owner users cannot access /api/me/branches/."""
    api_client.force_authenticate(user=users["phone_seller"])
    response = api_client.get(reverse("api_me_branches"))
    assert response.status_code == 403

    api_client.force_authenticate(user=users["accessory_seller"])
    response = api_client.get(reverse("api_me_branches"))
    assert response.status_code == 403


def test_me_branches_blocked_for_unauthenticated(api_client):
    """Unauthenticated request to /api/me/branches/ returns 401."""
    response = api_client.get(reverse("api_me_branches"))
    assert response.status_code == 401


# ---- /api/me/staff/ ----


def test_me_staff_returns_sellers_in_owned_branches(api_client, users, branches):
    """Owner staff endpoint returns phone and accessory sellers in owned branches."""
    api_client.force_authenticate(user=users["owner"])
    response = api_client.get(reverse("api_me_staff"))
    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    user_ids = {s["user_id"] for s in payload["data"]}
    assert users["phone_seller"].id in user_ids
    assert users["accessory_seller"].id in user_ids


def test_me_staff_does_not_return_non_seller_roles(api_client, users, branches):
    """Owner staff endpoint does not return other owners."""
    second_owner = _create_user("second_owner_staff")
    _assign_role(second_owner, branches["main"], models.BranchUser.ROLE_OWNER)

    api_client.force_authenticate(user=users["owner"])
    response = api_client.get(reverse("api_me_staff"))
    assert response.status_code == 200
    user_ids = {s["user_id"] for s in response.json()["data"]}
    assert second_owner.id not in user_ids


def test_me_staff_branch_filter_works(api_client, users, branches):
    """Optional branch filter returns sellers only from that branch."""
    other_seller = _create_user("other_branch_seller_me")
    _assign_role(users["owner"], branches["other"], models.BranchUser.ROLE_OWNER)
    _assign_role(other_seller, branches["other"], models.BranchUser.ROLE_PHONE_SELLER)

    api_client.force_authenticate(user=users["owner"])
    response = api_client.get(reverse("api_me_staff"), {"branch": branches["main"].id})
    assert response.status_code == 200
    user_ids = {s["user_id"] for s in response.json()["data"]}
    assert users["phone_seller"].id in user_ids
    assert other_seller.id not in user_ids

    response_other = api_client.get(reverse("api_me_staff"), {"branch": branches["other"].id})
    assert response_other.status_code == 200
    user_ids_other = {s["user_id"] for s in response_other.json()["data"]}
    assert other_seller.id in user_ids_other
    assert users["phone_seller"].id not in user_ids_other


def test_me_staff_branch_filter_for_non_owned_branch_returns_empty(api_client, users, branches):
    """Filtering by a non-owned branch returns empty result, not an error."""
    other_owner = _create_user("other_owner_staff_filter")
    other_branch = models.Branch.objects.create(name="Other Filter Branch", owner=other_owner)
    _assign_role(other_owner, other_branch, models.BranchUser.ROLE_OWNER)

    api_client.force_authenticate(user=users["owner"])
    response = api_client.get(reverse("api_me_staff"), {"branch": other_branch.id})
    assert response.status_code == 200
    assert len(response.json()["data"]) == 0


def test_me_staff_blocked_for_non_owner(api_client, users):
    """Non-owner users cannot access /api/me/staff/."""
    api_client.force_authenticate(user=users["phone_seller"])
    response = api_client.get(reverse("api_me_staff"))
    assert response.status_code == 403


def test_me_staff_blocked_for_unauthenticated(api_client):
    """Unauthenticated request to /api/me/staff/ returns 401."""
    response = api_client.get(reverse("api_me_staff"))
    assert response.status_code == 401


def test_me_staff_includes_role_and_branch_info(api_client, users, branches):
    """Staff list includes role, branch_id, and branch_name fields."""
    api_client.force_authenticate(user=users["owner"])
    response = api_client.get(reverse("api_me_staff"))
    assert response.status_code == 200
    staff = response.json()["data"]
    assert len(staff) >= 1
    for member in staff:
        assert "user_id" in member
        assert "username" in member
        assert "first_name" in member
        assert "last_name" in member
        assert "role" in member
        assert member["role"] in (
            models.BranchUser.ROLE_PHONE_SELLER,
            models.BranchUser.ROLE_ACCESSORY_SELLER,
        )
        assert "branch_id" in member
        assert "branch_name" in member
