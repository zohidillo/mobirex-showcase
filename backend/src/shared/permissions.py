from django.conf import settings
from django.utils.crypto import constant_time_compare
from django.utils.translation import gettext_lazy as _
from rest_framework.permissions import BasePermission
from rest_framework.exceptions import PermissionDenied

from src.core.models import Branch


def has_valid_support_request_x_key(request):
    """Return whether the request includes the configured support X-Key."""
    configured_key = getattr(settings, "SUPPORT_REQUEST_X_KEY", "")
    supplied_key = request.headers.get("X-Key", "")
    if not configured_key or not supplied_key:
        return False
    return constant_time_compare(str(supplied_key), str(configured_key))


class HasValidXKeyOrAuthenticated(BasePermission):
    """Allow authenticated users or external callers with the support X-Key."""

    message = _("Ruxsat yo‘q.")

    def has_permission(self, request, view):
        if request.user and request.user.is_authenticated:
            return True
        if has_valid_support_request_x_key(request):
            return True
        raise PermissionDenied(self.message)


def get_owner_branches(user):
    """Return branches the user owns through owner-role membership."""
    if not user or not getattr(user, "is_authenticated", False):
        return []

    branches = []
    if hasattr(user, "get_all_branches"):
        branches = [
            branch
            for branch in user.get_all_branches("OWNER")
            if branch and not getattr(branch, "is_deleted", False)
        ]

    if branches:
        unique = {}
        for branch in branches:
            unique[branch.id] = branch
        return list(unique.values())

    return list(Branch.objects.filter(owner=user, is_deleted=False))


def get_owner_branch_ids(user):
    """Return owned branch ids for the given user."""
    return [branch.id for branch in get_owner_branches(user)]


def user_can_access_owner_branch(user, branch):
    """Check whether the user can access the owner branch."""
    branch_id = getattr(branch, "id", branch)
    return branch_id in set(get_owner_branch_ids(user))


def get_primary_seller_branch(user):
    """Return the user's primary seller branch."""
    if not user or not getattr(user, "is_authenticated", False):
        return None
    if hasattr(user, "get_primary_branch"):
        return user.get_primary_branch("PHONE_SELLER") or user.get_primary_branch(
            "ACCESSORY_SELLER"
        )
    return None


def get_seller_domain_for_branch(user, branch):
    """Return the seller domain for the given branch."""
    if not user or not getattr(user, "is_authenticated", False) or branch is None:
        return None

    branch_id = getattr(branch, "id", branch)
    if hasattr(user, "has_role") and user.has_role("PHONE_SELLER", branch_id):
        return "PHONE"
    if hasattr(user, "has_role") and user.has_role("ACCESSORY_SELLER", branch_id):
        return "ACCESSORY"
    return None


def is_owner(user):
    """Return whether the user has owner access."""
    return bool(get_owner_branches(user))


def is_phone_seller(user):
    """Return whether the user has phone seller access."""
    return bool(
        user
        and getattr(user, "is_authenticated", False)
        and hasattr(user, "has_role")
        and user.has_role("PHONE_SELLER")
    )


def is_accessory_seller(user):
    """Return whether the user has accessory seller access."""
    return bool(
        user
        and getattr(user, "is_authenticated", False)
        and hasattr(user, "has_role")
        and user.has_role("ACCESSORY_SELLER")
    )


def is_superuser(user):
    """Return whether the user has superuser access."""
    return bool(
        user
        and getattr(user, "is_authenticated", False)
        and getattr(user, "is_superuser", False)
    )


def can_access_branch(user, branch):
    """Return whether the user can access the branch."""
    if not user or not getattr(user, "is_authenticated", False) or branch is None:
        return False

    branch_id = getattr(branch, "id", branch)
    if is_superuser(user) or getattr(user, "is_cashier", False):
        return True
    if branch_id in set(get_owner_branch_ids(user)):
        return True
    if hasattr(user, "has_role") and (
        user.has_role("PHONE_SELLER", branch_id) or user.has_role("ACCESSORY_SELLER", branch_id)
    ):
        return True
    return False


def user_matches_debt_domain(user, debt):
    """Return whether the user may access the debt's domain."""
    if debt is None:
        return False

    domain = getattr(debt, "domain", None)
    branch = getattr(debt, "branch", None)
    branch_id = getattr(branch, "id", branch)
    if is_superuser(user) or getattr(user, "is_cashier", False):
        return True
    if branch_id in set(get_owner_branch_ids(user)):
        return True

    if not domain:
        return get_seller_domain_for_branch(user, branch_id) == "PHONE"

    return get_seller_domain_for_branch(user, branch_id) == domain
