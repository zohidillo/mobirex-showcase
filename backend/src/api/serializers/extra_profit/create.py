"""Extra profit create serializers."""

from django.core.exceptions import PermissionDenied
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

import src.core.models as models
from src.services.extra_profit import ExtraProfitCreateService
from src.services.extra_profit.policy import get_seller_branch_and_capital_type
from src.shared.permissions import is_owner, is_phone_seller
from src.shared.validators import validate_positive_amount


class ExtraProfitCreateSerializer(serializers.ModelSerializer):
    """Create extra profit for a phone seller branch (phone capital only)."""

    branch = serializers.PrimaryKeyRelatedField(
        queryset=models.Branch.objects.filter(is_deleted=False),
        required=False,
        allow_null=True,
    )

    class Meta:
        model = models.ExtraProfit
        fields = [
            "branch",
            "amount",
            "note",
        ]

    def validate_amount(self, value):
        """Validate that the amount is positive."""
        return validate_positive_amount(value)

    def validate(self, attrs):
        """Validate branch selection against the acting user (phone seller only)."""
        user = self.context["request"].user

        if is_owner(user) or not is_phone_seller(user):
            raise PermissionDenied(_("Sizga bu amalni bajarish mumkin emas."))

        attrs.pop("branch", None)
        return attrs

    def create(self, validated_data):
        """Create extra profit through the existing service."""
        user = self.context["request"].user
        branch, _ = get_seller_branch_and_capital_type(user)
        if not branch:
            raise PermissionDenied(_("Filialga ruxsat yo'q."))
        validated_data["branch"] = branch
        return ExtraProfitCreateService.create_extra_profit(validated_data, created_by=user)
