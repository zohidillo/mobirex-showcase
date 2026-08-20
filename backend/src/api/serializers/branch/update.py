"""Branch update serializer."""

from rest_framework import serializers

import src.core.models as models


class BranchUpdateSerializer(serializers.ModelSerializer):
    """Update branches with the admin form fields."""

    owner = serializers.PrimaryKeyRelatedField(queryset=models.User.objects.filter(is_deleted=False))

    class Meta:
        model = models.Branch
        fields = ["name", "owner", "address", "is_active"]
