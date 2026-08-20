"""Branch-user create serializer."""

from django.db import transaction
from rest_framework import serializers

import src.core.models as models


class BranchUserCreateSerializer(serializers.ModelSerializer):
    """Create or revive branch role assignments."""

    user = serializers.PrimaryKeyRelatedField(queryset=models.User.objects.filter(is_deleted=False))
    branch = serializers.PrimaryKeyRelatedField(
        queryset=models.Branch.objects.filter(is_deleted=False)
    )

    class Meta:
        model = models.BranchUser
        fields = ["user", "branch", "role"]

    def create(self, validated_data):
        """Create the role assignment with the web flow semantics."""
        with transaction.atomic():
            existing = models.BranchUser.all_objects.filter(**validated_data).first()
            if existing:
                if existing.is_deleted:
                    existing.is_deleted = False
                    existing.save(update_fields=["is_deleted", "updated_at"])
                    return existing
                raise serializers.ValidationError(
                    {"non_field_errors": ["Bu filial roli allaqachon mavjud."]}
                )
            return models.BranchUser.objects.create(**validated_data)
