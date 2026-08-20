"""Transaction log serializers."""

from rest_framework import serializers

import src.core.models as models


class TransactionLogUserSerializer(serializers.ModelSerializer):
    """Serialize transaction-log user details."""

    class Meta:
        model = models.User
        fields = ["id", "username", "first_name", "last_name"]


class TransactionLogListSerializer(serializers.ModelSerializer):
    """List transaction logs with template-visible fields."""

    user = TransactionLogUserSerializer(read_only=True)
    user_id = serializers.IntegerField(read_only=True)
    transaction_type = serializers.CharField(source="type", read_only=True)
    transaction_type_display = serializers.ReadOnlyField(source="get_type_display")

    class Meta:
        model = models.TransactionLog
        fields = [
            "id",
            "user",
            "user_id",
            "transaction_type",
            "transaction_type_display",
            "amount",
            "balance_before",
            "balance_after",
            "charge_date",
            "charge_day",
            "added_at",
            "updated_at",
        ]
