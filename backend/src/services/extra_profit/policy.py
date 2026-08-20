from django.utils import timezone

import src.core.models as models
from src.shared.permissions import (
    get_owner_branches,
    is_owner,
    is_phone_seller,
    user_can_access_owner_branch,
)


CAPITAL_TYPE_PHONE = "phone"
CAPITAL_TYPE_ACCESSORY = "accessory"


def get_owned_branches_for_extra_profit(user):
    """Return branches visible to an owner for extra profit screens."""
    if not user or not getattr(user, "is_authenticated", False):
        return []

    branches = {}
    for branch in get_owner_branches(user):
        if branch and not getattr(branch, "is_deleted", False):
            branches[branch.id] = branch

    for branch in models.Branch.objects.filter(owner=user, is_deleted=False):
        branches[branch.id] = branch

    return list(branches.values())


def get_seller_branch_and_capital_type(user):
    """Return the phone seller branch and PHONE capital type for the acting user."""
    if is_phone_seller(user):
        branch = user.get_primary_branch(models.BranchUser.ROLE_PHONE_SELLER)
        if branch and user.has_role(models.BranchUser.ROLE_PHONE_SELLER, branch):
            return branch, CAPITAL_TYPE_PHONE

    return None, None


def get_seller_capital_type_for_branch(user, branch):
    """Return PHONE capital type if user is phone seller in branch, else None."""
    if not branch:
        return None
    if user.has_role(models.BranchUser.ROLE_PHONE_SELLER, branch):
        return CAPITAL_TYPE_PHONE
    return None


def get_extra_profit_capital_type(extra_profit):
    """Extra profit always affects PhoneCapital."""
    return CAPITAL_TYPE_PHONE


def filter_extra_profit_queryset_for_user(queryset, user):
    """Apply extra profit branch/domain visibility rules to a queryset."""
    if is_owner(user):
        branch_ids = [branch.id for branch in get_owned_branches_for_extra_profit(user)]
        if not branch_ids:
            return queryset.none()
        return queryset.filter(branch_id__in=branch_ids)

    if is_phone_seller(user):
        branch = user.get_primary_branch(models.BranchUser.ROLE_PHONE_SELLER)
        if not branch:
            return queryset.none()
        phone_seller_ids = set(
            models.BranchUser.objects.filter(
                branch=branch,
                role=models.BranchUser.ROLE_PHONE_SELLER,
                is_deleted=False,
            ).values_list("user_id", flat=True)
        )
        if getattr(branch, "owner_id", None):
            phone_seller_ids.add(branch.owner_id)
        return queryset.filter(branch=branch, created_by_id__in=phone_seller_ids)

    return queryset.none()


def is_current_month_extra_profit(extra_profit, reference_time=None):
    """Return whether the extra profit belongs to the current local month."""
    now = timezone.localtime(reference_time or timezone.now())
    added_at = timezone.localtime(extra_profit.added_at)
    return added_at.year == now.year and added_at.month == now.month


def can_create_extra_profit(user, branch):
    """Only phone sellers can create extra profit."""
    if not branch:
        return False
    return user.has_role(models.BranchUser.ROLE_PHONE_SELLER, branch)


def can_delete_extra_profit(user, extra_profit):
    """Return whether the user may delete the extra profit row."""
    if not is_current_month_extra_profit(extra_profit):
        return False

    branch = getattr(extra_profit, "branch", None)

    if is_owner(user) and user_can_access_owner_branch(user, branch):
        return True

    if user.has_role(models.BranchUser.ROLE_PHONE_SELLER, branch):
        return extra_profit.created_by_id == getattr(user, "id", None)

    return False
