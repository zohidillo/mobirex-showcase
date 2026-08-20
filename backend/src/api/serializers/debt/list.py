"""Debt list serializers."""

from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

import src.core.models as models


class DebtBranchSerializer(serializers.ModelSerializer):
    """Serialize debt branch details."""

    class Meta:
        model = models.Branch
        fields = ["id", "name", "address", "is_active"]


class DebtUserSerializer(serializers.ModelSerializer):
    """Serialize debt user details."""

    class Meta:
        model = models.User
        fields = ["id", "username"]


class DebtPaymentHistorySerializer(serializers.ModelSerializer):
    """Serialize payment history shown in the debt template."""

    paid_by = DebtUserSerializer(read_only=True)
    paid_by_id = serializers.IntegerField(read_only=True)

    class Meta:
        model = models.DebtPayment
        fields = [
            "id",
            "amount",
            "remaining_balance",
            "paid_by",
            "paid_by_id",
            "note",
            "added_at",
            "updated_at",
        ]


class DebtListSerializer(serializers.ModelSerializer):
    """Serialize open debts with template-visible fields."""

    branch = DebtBranchSerializer(read_only=True)
    created_by = DebtUserSerializer(read_only=True)
    branch_id = serializers.IntegerField(read_only=True)
    created_by_id = serializers.IntegerField(read_only=True)
    direction_display = serializers.ReadOnlyField(source="get_direction_display")
    payments = serializers.SerializerMethodField()

    class Meta:
        model = models.Debt
        fields = [
            "id",
            "f_name",
            "amount",
            "remaining_amount",
            "direction",
            "direction_display",
            "note",
            "branch",
            "branch_id",
            "created_by",
            "created_by_id",
            "payments",
            "added_at",
            "updated_at",
        ]

    @extend_schema_field(DebtPaymentHistorySerializer(many=True))
    def get_payments(self, obj):
        """Return payment history for the debt."""
        payments = getattr(obj, "prefetched_payments", None)
        if payments is None:
            payments = (
                obj.payments.filter(is_deleted=False)
                .select_related("paid_by")
                .order_by("added_at", "id")
            )
        serializer = DebtPaymentHistorySerializer(payments, many=True)
        return serializer.data


class DebtClosedListSerializer(DebtListSerializer):
    """Serialize closed debts with closure timestamp."""

    closed_at = serializers.DateTimeField(read_only=True)

    class Meta(DebtListSerializer.Meta):
        fields = DebtListSerializer.Meta.fields + ["closed_at"]
