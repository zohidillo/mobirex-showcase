"""Phone capital serializers."""

from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

import src.core.models as models


class PhoneCapitalBranchSerializer(serializers.ModelSerializer):
    """Serialize phone capital branch details."""

    class Meta:
        model = models.Branch
        fields = ["id", "name", "address", "is_active"]


class PhoneCapitalSerializer(serializers.ModelSerializer):
    """Serialize phone capital rows for the list response."""

    branch = PhoneCapitalBranchSerializer(read_only=True)
    branch_id = serializers.IntegerField(read_only=True)
    year = serializers.SerializerMethodField()
    month_number = serializers.SerializerMethodField()
    is_placeholder = serializers.BooleanField(read_only=True, default=False)
    added_at = serializers.SerializerMethodField()
    updated_at = serializers.SerializerMethodField()

    class Meta:
        model = models.PhoneCapital
        fields = [
            "id",
            "branch",
            "branch_id",
            "month",
            "month_number",
            "year",
            "invested_amount",
            "current_balance",
            "is_placeholder",
            "added_at",
            "updated_at",
        ]

    def get_year(self, obj) -> int | None:
        return obj.month.year if getattr(obj, "month", None) else None

    def get_month_number(self, obj) -> int | None:
        return obj.month.month if getattr(obj, "month", None) else None

    def get_added_at(self, obj) -> str | None:
        val = getattr(obj, "added_at", None)
        return val.isoformat() if val else None

    def get_updated_at(self, obj) -> str | None:
        val = getattr(obj, "updated_at", None)
        return val.isoformat() if val else None


class PhoneCapitalCreateSerializer(serializers.Serializer):
    """Validate phone capital investment input.

    month and year must not be sent by the client; backend always uses current month.
    """

    branch = serializers.IntegerField()
    amount = serializers.DecimalField(max_digits=14, decimal_places=2)

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError(_("Miqdor musbat bo'lishi kerak."))
        return value

    def validate(self, data):
        forbidden = set(self.initial_data.keys()) & {"month", "year"}
        if forbidden:
            raise serializers.ValidationError(
                _("Oy yoki yil kiritish mumkin emas.")
            )
        return data


class PhoneCapitalResetSerializer(serializers.Serializer):
    """Validate phone capital reset input."""

    branch = serializers.IntegerField()
