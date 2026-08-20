"""Branch-user API tests."""

import pytest
from django.urls import reverse

from src.core import models


pytestmark = pytest.mark.django_db


def test_superadmin_can_assign_branch_role(api_client, users, branches):
    """Superadmin can create branch role assignments."""
    api_client.force_authenticate(user=users["admin"])

    response = api_client.post(
        reverse("api_branch_user_list_create"),
        {
            "user": users["outsider"].id,
            "branch": branches["other"].id,
            "role": models.BranchUser.ROLE_PHONE_SELLER,
        },
        format="json",
    )

    assert response.status_code == 201
    assignment = models.BranchUser.objects.get(
        user=users["outsider"],
        branch=branches["other"],
        role=models.BranchUser.ROLE_PHONE_SELLER,
    )
    assert assignment.is_deleted is False


def test_invalid_role_is_blocked(api_client, users, branches):
    """Invalid branch roles are rejected."""
    api_client.force_authenticate(user=users["admin"])

    response = api_client.post(
        reverse("api_branch_user_list_create"),
        {
            "user": users["outsider"].id,
            "branch": branches["other"].id,
            "role": "INVALID_ROLE",
        },
        format="json",
    )

    assert response.status_code == 400
    assert response.json()["success"] is False


def test_unauthorized_role_assignment_is_blocked(api_client, users, branches):
    """Only superadmin can assign branch roles."""
    api_client.force_authenticate(user=users["owner"])

    response = api_client.post(
        reverse("api_branch_user_list_create"),
        {
            "user": users["outsider"].id,
            "branch": branches["other"].id,
            "role": models.BranchUser.ROLE_OWNER,
        },
        format="json",
    )

    assert response.status_code == 403


def test_branch_user_update_and_revive_work(api_client, users, branches):
    """Branch role assignments can be updated and deleted rows are revived."""
    assignment = models.BranchUser.objects.create(
        user=users["outsider"],
        branch=branches["main"],
        role=models.BranchUser.ROLE_OWNER,
    )
    deleted_assignment = models.BranchUser.objects.create(
        user=users["outsider"],
        branch=branches["other"],
        role=models.BranchUser.ROLE_ACCESSORY_SELLER,
        is_deleted=True,
    )
    api_client.force_authenticate(user=users["admin"])

    patch_response = api_client.patch(
        reverse("api_branch_user_detail", args=[assignment.id]),
        {"role": models.BranchUser.ROLE_PHONE_SELLER},
        format="json",
    )
    assert patch_response.status_code == 200
    assignment.refresh_from_db()
    assert assignment.role == models.BranchUser.ROLE_PHONE_SELLER

    revive_response = api_client.post(
        reverse("api_branch_user_list_create"),
        {
            "user": users["outsider"].id,
            "branch": branches["other"].id,
            "role": models.BranchUser.ROLE_ACCESSORY_SELLER,
        },
        format="json",
    )
    assert revive_response.status_code == 201
    deleted_assignment.refresh_from_db()
    assert deleted_assignment.is_deleted is False
