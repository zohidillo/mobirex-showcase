"""Branch-user list serializers."""

from rest_framework import serializers

import src.core.models as models


class BranchUserListUserSerializer(serializers.ModelSerializer):
    """Serialize branch-user user details."""

    class Meta:
        model = models.User
        fields = ["id", "username", "first_name", "last_name"]


class BranchUserListBranchSerializer(serializers.ModelSerializer):
    """Serialize branch-user branch details."""

    class Meta:
        model = models.Branch
        fields = ["id", "name", "address", "is_active"]


class BranchUserListSerializer(serializers.ModelSerializer):
    """List branch role assignments."""

    user = BranchUserListUserSerializer(read_only=True)
    branch = BranchUserListBranchSerializer(read_only=True)
    user_id = serializers.IntegerField(read_only=True)
    branch_id = serializers.IntegerField(read_only=True)
    role_display = serializers.ReadOnlyField(source="get_role_display")

    class Meta:
        model = models.BranchUser
        fields = [
            "id",
            "user",
            "user_id",
            "branch",
            "branch_id",
            "role",
            "role_display",
            "added_at",
            "updated_at",
        ]
