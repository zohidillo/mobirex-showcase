"""User update serializer."""

from rest_framework import serializers

import src.core.models as models


class UserUpdateSerializer(serializers.ModelSerializer):
    """Update users with the same fields as the admin form."""

    class Meta:
        model = models.User
        fields = [
            "username",
            "first_name",
            "last_name",
            "email",
            "phone",
            "daily_fee",
            "is_active",
            "is_staff",
            "is_superuser",
            "is_vip",
            "is_cashier",
        ]
