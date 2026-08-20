"""Current-user serializers for mobile auth/settings flows."""

from rest_framework import serializers

import src.core.models as models
from src.services.billing import AccountAccessService, GraceStatusService


ROLE_PRIORITY = {
    models.BranchUser.ROLE_OWNER: 0,
    models.BranchUser.ROLE_PHONE_SELLER: 1,
    models.BranchUser.ROLE_ACCESSORY_SELLER: 2,
}


class MeRoleSerializer(serializers.Serializer):
    """Serialize a branch-role pair for the current user."""

    branch_id = serializers.IntegerField()
    branch_name = serializers.CharField()
    role = serializers.CharField()


class MeBranchSerializer(serializers.Serializer):
    """Serialize a current-user branch summary."""

    id = serializers.IntegerField()
    name = serializers.CharField()
    role = serializers.CharField()


class UserContextBuilder:
    """Build the current user's mobile app context."""

    @classmethod
    def _upsert_branch(cls, branch_map, branch, role):
        current = branch_map.get(branch.id)
        candidate = {
            "id": branch.id,
            "name": branch.name,
            "role": role,
        }
        if current is None:
            branch_map[branch.id] = candidate
            return

        current_priority = ROLE_PRIORITY.get(current["role"], 999)
        candidate_priority = ROLE_PRIORITY.get(role, 999)
        if candidate_priority < current_priority:
            branch_map[branch.id] = candidate

    @classmethod
    def build(cls, user):
        role_items = []
        branch_map = {}
        owner_role_branch_ids = set()

        assignments = (
            user.branch_roles.filter(is_deleted=False, branch__is_deleted=False)
            .select_related("branch")
            .order_by("branch_id", "role", "id")
        )
        for assignment in assignments:
            branch = assignment.branch
            role_items.append(
                {
                    "branch_id": branch.id,
                    "branch_name": branch.name,
                    "role": assignment.role,
                }
            )
            cls._upsert_branch(branch_map, branch, assignment.role)
            if assignment.role == models.BranchUser.ROLE_OWNER:
                owner_role_branch_ids.add(branch.id)

        for branch in user.owned_branches.filter(is_deleted=False).order_by("id"):
            if branch.id not in owner_role_branch_ids:
                role_items.append(
                    {
                        "branch_id": branch.id,
                        "branch_name": branch.name,
                        "role": models.BranchUser.ROLE_OWNER,
                    }
                )
            cls._upsert_branch(branch_map, branch, models.BranchUser.ROLE_OWNER)

        role_items.sort(key=lambda item: (item["branch_id"], ROLE_PRIORITY.get(item["role"], 999)))
        branches = sorted(branch_map.values(), key=lambda item: item["id"])
        return {
            "roles": role_items,
            "branches": branches,
        }


class MeSerializer(serializers.ModelSerializer):
    """Return the authenticated user's mobile profile and app context."""

    full_name = serializers.SerializerMethodField()
    has_pin = serializers.ReadOnlyField()
    pin_enabled = serializers.ReadOnlyField(source="has_pin")
    roles = serializers.SerializerMethodField()
    branches = serializers.SerializerMethodField()
    account_status_display = serializers.SerializerMethodField()
    billing = serializers.SerializerMethodField()

    class Meta:
        model = models.User
        fields = [
            "id",
            "username",
            "first_name",
            "last_name",
            "full_name",
            "phone",
            "balance",
            "is_vip",
            "account_status",
            "account_status_display",
            "billing",
            "is_superuser",
            "is_cashier",
            "theme",
            "has_pin",
            "pin_enabled",
            "roles",
            "branches",
        ]

    def get_full_name(self, obj):
        """Return the user's display name."""
        return obj.get_full_name().strip()

    def get_account_status_display(self, obj):
        """Return the human-readable account status label."""
        return obj.get_account_status_display()

    def get_billing(self, obj):
        """Return the current billing/subscription state for the mobile UI.

        Read-only: reuses ``AccountAccessService`` for the exact same messages
        the middleware/login already produce (``persist=False`` — no mutation).
        """
        decision = AccountAccessService.evaluate_user(obj, persist=False)
        status = decision.status
        is_grace = status == GraceStatusService.GRACE
        is_blocked = status == GraceStatusService.BLOCKED

        grace_start = getattr(obj, "grace_start_date", None)
        return {
            "status": status,
            "is_blocked": is_blocked,
            "is_grace": is_grace,
            "warning_message": decision.warning_message or "",
            "blocked_message": decision.blocked_message or "",
            "grace_start_date": grace_start.isoformat() if grace_start else None,
            "grace_days_left": GraceStatusService.grace_days_left(obj) if is_grace else None,
        }

    def _get_context_data(self, obj):
        cache = getattr(self, "_mobile_context_cache", None)
        if cache is None or cache["user_id"] != obj.id:
            built = UserContextBuilder.build(obj)
            cache = {
                "user_id": obj.id,
                **built,
            }
            self._mobile_context_cache = cache
        return cache

    def get_roles(self, obj):
        """Return branch-role assignments for the current user."""
        return self._get_context_data(obj)["roles"]

    def get_branches(self, obj):
        """Return a branch summary list for the current user."""
        return self._get_context_data(obj)["branches"]


class MeSettingsSerializer(serializers.ModelSerializer):
    """Update self-managed mobile settings for the authenticated user."""

    class Meta:
        model = models.User
        fields = [
            "username",
            "theme",
        ]

