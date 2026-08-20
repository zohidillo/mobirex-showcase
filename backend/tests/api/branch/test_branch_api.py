"""Branch API tests."""

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


def test_superadmin_can_list_create_and_update_branches(api_client, users):
    """Superadmin can manage branches through the API."""
    api_client.force_authenticate(user=users["admin"])

    list_response = api_client.get(reverse("api_branch_list_create"))
    assert list_response.status_code == 200
    _paginated_data(list_response)

    create_response = api_client.post(
        reverse("api_branch_list_create"),
        {
            "name": "API Branch",
            "owner": users["owner"].id,
            "address": "API address",
            "is_active": True,
        },
        format="json",
    )
    assert create_response.status_code == 201
    branch_id = create_response.json()["data"]["id"]

    patch_response = api_client.patch(
        reverse("api_branch_detail", args=[branch_id]),
        {
            "name": "Updated API Branch",
            "is_active": False,
        },
        format="json",
    )

    assert patch_response.status_code == 200
    assert patch_response.json()["data"]["name"] == "Updated API Branch"
    assert patch_response.json()["data"]["is_active"] is False


def test_unauthorized_roles_cannot_manage_branches(api_client, users):
    """Non-admin users cannot access branch management APIs."""
    api_client.force_authenticate(user=users["owner"])

    list_response = api_client.get(reverse("api_branch_list_create"))
    create_response = api_client.post(
        reverse("api_branch_list_create"),
        {
            "name": "Blocked Branch",
            "owner": users["owner"].id,
            "is_active": True,
        },
        format="json",
    )

    assert list_response.status_code == 403
    assert create_response.status_code == 403
