"""User list serializers."""

from rest_framework import serializers

import src.core.models as models


class UserListSerializer(serializers.ModelSerializer):
    """List users with admin-visible account fields."""

    full_name = serializers.SerializerMethodField()
    account_status_display = serializers.ReadOnlyField(source="get_account_status_display")

    class Meta:
        model = models.User
        fields = [
            "id",
            "username",
            "first_name",
            "last_name",
            "full_name",
            "balance",
            "daily_fee",
            "is_active",
            "is_cashier",
            "is_superuser",
            "account_status",
            "account_status_display",
            "added_at",
            "updated_at",
        ]

    def get_full_name(self, obj) -> str:
        """Return the user's full name."""
        return f"{obj.first_name} {obj.last_name}".strip()
