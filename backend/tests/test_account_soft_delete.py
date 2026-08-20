"""Self-service account soft-delete.

Apple App Store requires that a user can delete their own account from inside
the app. We do NOT erase data — the account is renamed, deactivated and marked
deleted, while the user's business records (debts, sales, phones, capital) stay
untouched so the owner's statistics never break.
"""

from decimal import Decimal

import pytest
from django.urls import reverse
from rest_framework_simplejwt.tokens import RefreshToken

from src.core import models
from src.services.user import UserDeleteService
from src.shared.demo import DEMO_ACTION_BLOCKED_MESSAGE


pytestmark = pytest.mark.django_db


def _body(response):
    """Flatten the standard response envelope for message assertions."""
    payload = response.json()
    return payload.get("error") or payload.get("detail") or ""


# --------------------------------------------------------------------------- #
# Service layer                                                                #
# --------------------------------------------------------------------------- #


def test_service_renames_and_deactivates():
    user = models.User.objects.create_user(username="seller_one", password="pass123")

    UserDeleteService.soft_delete_account(user)

    user.refresh_from_db()
    assert user.username == "seller_one-deleted"
    assert user.is_deleted is True
    assert user.is_active is False
    assert user.deleted_at is not None


def test_service_preserves_business_records(branches, users):
    """Soft-delete must not touch the user's debts/sales — only the 4 fields."""
    seller = users["phone_seller"]
    for index in range(3):
        models.Debt.objects.create(
            branch=branches["main"],
            created_by=seller,
            f_name=f"Debt {index}",
            amount=Decimal("100.00"),
            remaining_amount=Decimal("100.00"),
            direction="WE_GAVE",
            note="kept",
        )
    before = models.Debt.objects.filter(created_by=seller).count()
    assert before == 3

    UserDeleteService.soft_delete_account(seller)

    after = models.Debt.objects.filter(created_by=seller).count()
    assert after == before  # records survive, still owned by the (renamed) user


def test_service_username_collision_appends_counter():
    """When `<name>-deleted` is taken, fall through to `-deleted-1`."""
    models.User.objects.create_user(username="victim-deleted", password="pass123")
    user = models.User.objects.create_user(username="victim", password="pass123")

    UserDeleteService.soft_delete_account(user)

    user.refresh_from_db()
    assert user.username == "victim-deleted-1"


def test_service_username_collision_second_counter():
    """Two taken variants push to `-deleted-2`."""
    models.User.objects.create_user(username="busy-deleted", password="pass123")
    models.User.objects.create_user(username="busy-deleted-1", password="pass123")
    user = models.User.objects.create_user(username="busy", password="pass123")

    UserDeleteService.soft_delete_account(user)

    user.refresh_from_db()
    assert user.username == "busy-deleted-2"


# --------------------------------------------------------------------------- #
# API endpoint                                                                 #
# --------------------------------------------------------------------------- #


def test_api_unauthenticated_returns_401(api_client):
    response = api_client.post(reverse("api_account_delete"), {}, format="json")
    assert response.status_code == 401


def test_api_authenticated_deletes_account(api_client):
    user = models.User.objects.create_user(username="mobile_user", password="pass123")
    api_client.force_authenticate(user=user)

    response = api_client.post(reverse("api_account_delete"), {}, format="json")

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["message"] == "Hisobingiz o‘chirildi."

    user.refresh_from_db()
    assert user.username == "mobile_user-deleted"
    assert user.is_deleted is True
    assert user.is_active is False
    assert user.deleted_at is not None


def test_api_demo_account_cannot_delete(api_client):
    demo = models.User.objects.create_user(username="demo_owner", password="pass123")
    api_client.force_authenticate(user=demo)

    response = api_client.post(reverse("api_account_delete"), {}, format="json")

    assert response.status_code == 403
    assert DEMO_ACTION_BLOCKED_MESSAGE in _body(response)
    demo.refresh_from_db()
    assert demo.username == "demo_owner"
    assert demo.is_deleted is False
    assert demo.is_active is True


def test_api_blacklists_refresh_token(api_client):
    user = models.User.objects.create_user(username="logout_user", password="pass123")
    refresh = RefreshToken.for_user(user)
    api_client.force_authenticate(user=user)

    response = api_client.post(
        reverse("api_account_delete"), {"refresh": str(refresh)}, format="json"
    )
    assert response.status_code == 200

    # The blacklisted refresh token can no longer mint new access tokens.
    api_client.force_authenticate(user=None)
    refresh_response = api_client.post(
        reverse("token_refresh"), {"refresh": str(refresh)}, format="json"
    )
    assert refresh_response.status_code == 401


def test_api_invalid_refresh_token_still_deletes(api_client):
    """A bad/expired refresh token must not block the deletion itself."""
    user = models.User.objects.create_user(username="bad_token_user", password="pass123")
    api_client.force_authenticate(user=user)

    response = api_client.post(
        reverse("api_account_delete"), {"refresh": "not-a-real-token"}, format="json"
    )

    assert response.status_code == 200
    user.refresh_from_db()
    assert user.is_deleted is True


# --------------------------------------------------------------------------- #
# Login is blocked after deletion                                             #
# --------------------------------------------------------------------------- #


def test_deleted_user_cannot_login(api_client):
    user = models.User.objects.create_user(username="ex_user", password="pass123")
    UserDeleteService.soft_delete_account(user)

    response = api_client.post(
        reverse("api_auth_login"),
        {"username": "ex_user-deleted", "password": "pass123"},
        format="json",
    )
    assert response.status_code == 401


# --------------------------------------------------------------------------- #
# Salary cannot be paid to a soft-deleted seller (two-layer defense)          #
# --------------------------------------------------------------------------- #


def test_salary_cannot_be_paid_to_deleted_seller(api_client, users, branches):
    seller = users["phone_seller"]
    UserDeleteService.soft_delete_account(seller)

    api_client.force_authenticate(user=users["owner"])
    response = api_client.post(
        reverse("api_salary_list_create"),
        {"employee": seller.id, "amount": "500.00", "note": "should fail"},
        format="json",
    )

    assert response.status_code in (400, 403)
    assert not models.Salary.objects.filter(employee=seller).exists()


def test_salary_validate_guard_rejects_deleted_employee(users):
    """Directly exercise the second-layer guard in serializer.validate()."""
    from rest_framework.test import APIRequestFactory
    from django.core.exceptions import PermissionDenied

    from src.api.serializers.salary.create import SalaryCreateSerializer

    seller = users["phone_seller"]
    seller.is_deleted = True
    seller.save(update_fields=["is_deleted"])

    request = APIRequestFactory().post("/api/salary/")
    request.user = users["owner"]

    serializer = SalaryCreateSerializer(context={"request": request})
    with pytest.raises(PermissionDenied):
        serializer.validate({"employee": seller, "amount": Decimal("100.00")})
