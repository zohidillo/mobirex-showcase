"""Serializer for owner's own branches."""

from rest_framework import serializers

import src.core.models as models


class OwnerBranchSerializer(serializers.ModelSerializer):
    """Serialize a branch for the owner /me/branches/ endpoint."""

    class Meta:
        model = models.Branch
        fields = ["id", "name", "address", "is_active"]
