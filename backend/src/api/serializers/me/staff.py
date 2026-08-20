"""Serializer for owner's staff list."""

from rest_framework import serializers

import src.core.models as models


class OwnerStaffSerializer(serializers.ModelSerializer):
    """Serialize a BranchUser row for the owner /me/staff/ endpoint."""

    user_id = serializers.IntegerField(source="user.id", read_only=True)
    username = serializers.CharField(source="user.username", read_only=True)
    first_name = serializers.CharField(source="user.first_name", read_only=True)
    last_name = serializers.CharField(source="user.last_name", read_only=True)
    branch_id = serializers.IntegerField(source="branch.id", read_only=True)
    branch_name = serializers.CharField(source="user.username", read_only=True)

    class Meta:
        model = models.BranchUser
        fields = [
            "user_id",
            "username",
            "first_name",
            "last_name",
            "role",
            "branch_id",
            "branch_name",
        ]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["branch_name"] = instance.branch.name
        return data
