"""Expense create serializers."""

from django.core.exceptions import PermissionDenied
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

import src.core.models as models
from src.services.expense import ExpenseCreateService
from src.shared.permissions import (
    is_accessory_seller,
    is_phone_seller,
)
from src.shared.validators import validate_positive_amount


class ExpenseCreateSerializer(serializers.ModelSerializer):
    """Create expenses with the same branch rules as web."""

    branch = serializers.PrimaryKeyRelatedField(
        queryset=models.Branch.objects.filter(is_deleted=False),
        required=False,
        allow_null=True,
    )
    created_for = serializers.PrimaryKeyRelatedField(
        queryset=models.User.objects.filter(is_deleted=False),
        required=False,
        allow_null=True,
    )

    class Meta:
        model = models.Expense
        fields = [
            "branch",
            "created_for",
            "type",
            "amount",
            "note",
        ]

    def validate_amount(self, value):
        """Validate that the amount is positive."""
        return validate_positive_amount(value)

    def validate(self, attrs):
        """Validate access to the requested expense branch."""
        user = self.context["request"].user
        if not (is_phone_seller(user) or is_accessory_seller(user)):
            raise PermissionDenied(_("Sizga bu amalni bajarish mumkin emas."))

        attrs.pop("branch", None)
        attrs.pop("created_for", None)
        return attrs

    def create(self, validated_data):
        """Create an expense through the existing service."""
        user = self.context["request"].user
        data = dict(validated_data)
        branch = user.get_primary_branch("PHONE_SELLER") or user.get_primary_branch(
            "ACCESSORY_SELLER"
        )
        if not branch:
            raise PermissionDenied(_("Filialga ruxsat yo‘q."))

        data["branch"] = branch
        return ExpenseCreateService.create_expense(data, created_by=user)
