"""User detail serializers."""

from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

import src.core.models as models
from src.api.serializers.user.list import UserListSerializer


class UserRoleBranchSerializer(serializers.ModelSerializer):
    """Serialize a branch summary for user details."""

    class Meta:
        model = models.Branch
        fields = ["id", "name", "address", "is_active"]


class UserBranchRoleSerializer(serializers.ModelSerializer):
    """Serialize branch-role assignments for a user."""

    branch = UserRoleBranchSerializer(read_only=True)
    branch_id = serializers.IntegerField(read_only=True)
    role_display = serializers.ReadOnlyField(source="get_role_display")

    class Meta:
        model = models.BranchUser
        fields = [
            "id",
            "branch",
            "branch_id",
            "role",
            "role_display",
            "added_at",
            "updated_at",
        ]


class UserOwnedBranchSerializer(serializers.ModelSerializer):
    """Serialize owned branches for a user."""

    class Meta:
        model = models.Branch
        fields = ["id", "name", "address", "is_active", "added_at"]


class UserDetailSerializer(UserListSerializer):
    """Return admin detail data for a single user."""

    email = serializers.EmailField(read_only=True)
    phone = serializers.CharField(read_only=True)
    is_staff = serializers.BooleanField(read_only=True)
    is_vip = serializers.BooleanField(read_only=True)
    grace_start_date = serializers.DateField(read_only=True)
    branch_roles = serializers.SerializerMethodField()
    owned_branches = UserOwnedBranchSerializer(read_only=True, many=True)

    class Meta(UserListSerializer.Meta):
        fields = UserListSerializer.Meta.fields + [
            "email",
            "phone",
            "is_staff",
            "is_vip",
            "grace_start_date",
            "branch_roles",
            "owned_branches",
        ]

    @extend_schema_field(UserBranchRoleSerializer(many=True))
    def get_branch_roles(self, obj):
        """Return active branch roles for the user."""
        queryset = obj.branch_roles.filter(is_deleted=False).select_related("branch").order_by("role")
        return UserBranchRoleSerializer(queryset, many=True).data
