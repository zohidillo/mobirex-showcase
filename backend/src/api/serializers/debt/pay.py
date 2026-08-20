"""Debt payment serializers."""

from rest_framework import serializers

import src.core.models as models
from src.api.serializers.debt.list import DebtUserSerializer
from src.shared.validators import validate_debt_payment


class DebtPaySerializer(serializers.ModelSerializer):
    """Pay debt with positive non-overpay validation."""

    class Meta:
        model = models.DebtPayment
        fields = [
            "amount",
            "note",
        ]

    def validate_amount(self, value):
        """Validate the payment amount against the debt balance."""
        debt = self.context["debt"]
        return validate_debt_payment(debt, value)


class DebtPaymentSerializer(serializers.ModelSerializer):
    """Serialize debt payment details."""

    paid_by = DebtUserSerializer(read_only=True)
    paid_by_id = serializers.IntegerField(read_only=True)
    debt_id = serializers.IntegerField(read_only=True)
    debt_remaining_amount = serializers.DecimalField(
        source="debt.remaining_amount",
        max_digits=14,
        decimal_places=2,
        read_only=True,
    )

    class Meta:
        model = models.DebtPayment
        fields = [
            "id",
            "debt_id",
            "amount",
            "remaining_balance",
            "debt_remaining_amount",
            "paid_by",
            "paid_by_id",
            "note",
            "added_at",
            "updated_at",
        ]
