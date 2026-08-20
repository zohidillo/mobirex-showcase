"""Branch create serializer."""

from rest_framework import serializers

import src.core.models as models
from src.services.branch import BranchCreateService


class BranchCreateSerializer(serializers.ModelSerializer):
    """Create branches through the existing branch service."""

    owner = serializers.PrimaryKeyRelatedField(queryset=models.User.objects.filter(is_deleted=False))

    class Meta:
        model = models.Branch
        fields = ["name", "owner", "address", "is_active"]

    def create(self, validated_data):
        """Create a branch with the existing service."""
        return BranchCreateService.create_branch(
            validated_data,
            created_by=self.context["request"].user,
        )
