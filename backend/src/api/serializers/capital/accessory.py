"""Accessory capital serializers."""

from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

import src.core.models as models
from src.services.accessory import AccessoryAnalyticsService


class AccessoryCapitalBranchSerializer(serializers.ModelSerializer):
    """Serialize accessory capital branch details."""

    class Meta:
        model = models.Branch
        fields = ["id", "name", "address", "is_active"]


class AccessoryCapitalSerializer(serializers.ModelSerializer):
    """Serialize accessory capital rows with inventory value."""

    branch = AccessoryCapitalBranchSerializer(read_only=True)
    branch_id = serializers.IntegerField(read_only=True)
    year = serializers.SerializerMethodField()
    month_number = serializers.SerializerMethodField()
    inventory_value = serializers.SerializerMethodField()

    class Meta:
        model = models.AccessoryCapital
        fields = [
            "id",
            "branch",
            "branch_id",
            "month",
            "month_number",
            "year",
            "invested_amount",
            "current_balance",
            "inventory_value",
            "added_at",
            "updated_at",
        ]

    def get_year(self, obj) -> int | None:
        return obj.month.year if getattr(obj, "month", None) else None

    def get_month_number(self, obj) -> int | None:
        return obj.month.month if getattr(obj, "month", None) else None

    @extend_schema_field(serializers.CharField())
    def get_inventory_value(self, obj) -> str:
        """Return the branch inventory value (cached per branch within request)."""
        cache = self.context.setdefault("inventory_value_cache", {})
        branch_id = getattr(obj, "branch_id", None)
        if branch_id not in cache:
            cache[branch_id] = AccessoryAnalyticsService.get_inventory_value(obj.branch)
        return f"{cache[branch_id]:.2f}"
