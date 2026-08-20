"""Billing payment serializers."""

from rest_framework import serializers

import src.core.models as models
from src.services.billing import PaymentApplyService
from src.shared.validators import validate_positive_amount


class BillingPaymentUserSerializer(serializers.ModelSerializer):
    """Serialize payment-related user details."""

    class Meta:
        model = models.User
        fields = ["id", "username", "first_name", "last_name"]


class BillingPaymentListSerializer(serializers.ModelSerializer):
    """List cashier payments with template-visible fields."""

    user = BillingPaymentUserSerializer(read_only=True)
    added_by = BillingPaymentUserSerializer(read_only=True)
    user_id = serializers.IntegerField(read_only=True)
    added_by_id = serializers.IntegerField(read_only=True)
    payment_type_display = serializers.ReadOnlyField(source="get_payment_type_display")

    class Meta:
        model = models.Payment
        fields = [
            "id",
            "user",
            "user_id",
            "amount",
            "payment_type",
            "payment_type_display",
            "added_by",
            "added_by_id",
            "added_at",
            "updated_at",
        ]


class BillingPaymentCreateSerializer(serializers.ModelSerializer):
    """Create cashier payments with the existing billing service."""

    user = serializers.PrimaryKeyRelatedField(
        queryset=models.User.objects.filter(is_deleted=False).order_by("username")
    )

    class Meta:
        model = models.Payment
        fields = ["user", "amount", "payment_type"]

    def validate_amount(self, value):
        """Validate that the payment amount is positive."""
        return validate_positive_amount(value)

    def create(self, validated_data):
        """Create a payment through the existing billing service."""
        return PaymentApplyService.create_payment(
            user=validated_data["user"],
            amount=validated_data["amount"],
            payment_type=validated_data["payment_type"],
            added_by=self.context["request"].user,
        )
