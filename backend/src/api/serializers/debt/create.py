"""Debt create serializers."""

from django.core.exceptions import PermissionDenied
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

import src.core.models as models
from src.services.debt import DebtCreateService
from src.shared.permissions import get_primary_seller_branch, is_accessory_seller, is_owner, is_phone_seller
from src.shared.validators import validate_positive_amount


class DebtCreateSerializer(serializers.ModelSerializer):
    """Create debt. Only sellers allowed. Branch auto assigned."""

    class Meta:
        model = models.Debt
        fields = [
            "f_name",
            "amount",
            "direction",
            "note",
        ]

    def validate_amount(self, value):
        """Validate that the debt amount is positive."""
        return validate_positive_amount(value)

    def validate(self, attrs):
        """Validate the acting user for debt creation."""
        user = self.context["request"].user

        if is_owner(user):
            raise PermissionDenied(_("Sizga bu amalni bajarish mumkin emas."))
        if not (is_phone_seller(user) or is_accessory_seller(user)):
            raise PermissionDenied(_("Sizga bu amalni bajarish mumkin emas."))
        return attrs

    def create(self, validated_data):
        """Create a debt through the existing service."""
        user = self.context["request"].user
        branch = get_primary_seller_branch(user)
        if not branch:
            raise PermissionDenied(_("Sizga bu amalni bajarish mumkin emas."))

        return DebtCreateService.create_debt(
            branch=branch,
            f_name=validated_data.get("f_name"),
            amount=validated_data.get("amount"),
            direction=validated_data.get("direction"),
            created_by=user,
            note=validated_data.get("note"),
        )
