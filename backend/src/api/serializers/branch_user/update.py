"""Branch-user update serializer."""

from rest_framework import serializers

import src.core.models as models


class BranchUserUpdateSerializer(serializers.ModelSerializer):
    """Update active branch role assignments safely."""

    user = serializers.PrimaryKeyRelatedField(queryset=models.User.objects.filter(is_deleted=False))
    branch = serializers.PrimaryKeyRelatedField(
        queryset=models.Branch.objects.filter(is_deleted=False)
    )

    class Meta:
        model = models.BranchUser
        fields = ["user", "branch", "role"]

    def validate(self, attrs):
        """Block duplicate role assignments before hitting the database."""
        attrs = super().validate(attrs)
        instance = self.instance
        user = attrs.get("user", instance.user)
        branch = attrs.get("branch", instance.branch)
        role = attrs.get("role", instance.role)

        duplicate = models.BranchUser.all_objects.filter(
            user=user,
            branch=branch,
            role=role,
        ).exclude(pk=instance.pk)
        if duplicate.exists():
            raise serializers.ValidationError(
                {"non_field_errors": ["Bu filial roli allaqachon mavjud."]}
            )
        return attrs
