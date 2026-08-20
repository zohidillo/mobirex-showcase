"""Branch list serializers."""

from rest_framework import serializers

import src.core.models as models


class BranchOwnerSerializer(serializers.ModelSerializer):
    """Serialize branch owner details."""

    class Meta:
        model = models.User
        fields = ["id", "username", "first_name", "last_name"]


class BranchListSerializer(serializers.ModelSerializer):
    """List branches with admin-visible fields."""

    owner = BranchOwnerSerializer(read_only=True)
    owner_id = serializers.IntegerField(read_only=True)

    class Meta:
        model = models.Branch
        fields = [
            "id",
            "name",
            "owner",
            "owner_id",
            "address",
            "is_active",
            "added_at",
            "updated_at",
        ]
