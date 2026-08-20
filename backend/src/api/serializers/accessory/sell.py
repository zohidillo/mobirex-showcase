from rest_framework import serializers

import src.core.models as models
from src.api.serializers.accessory.list import (
    AccessoryListSerializer,
    BranchSerializer,
    UserSummarySerializer,
)
from src.shared.validators import check_stock_available


class AccessorySellSerializer(serializers.ModelSerializer):
    """Validate accessory sell payloads."""

    class Meta:
        model = models.AccessorySale
        fields = ["quantity", "total_price"]

    def validate_quantity(self, value):
        """Validate requested accessory quantity."""
        accessory = self.context["accessory"]
        return int(check_stock_available(accessory, value))


class AccessorySaleSerializer(serializers.ModelSerializer):
    """Serialize accessory sales with template-visible fields."""

    branch = BranchSerializer(read_only=True)
    sold_by = UserSummarySerializer(read_only=True)
    accessory = AccessoryListSerializer(read_only=True)
    branch_id = serializers.IntegerField(read_only=True)
    sold_by_id = serializers.IntegerField(read_only=True)
    accessory_id = serializers.IntegerField(read_only=True)

    class Meta:
        model = models.AccessorySale
        fields = [
            "id",
            "accessory",
            "accessory_id",
            "branch",
            "branch_id",
            "quantity",
            "unit_cost",
            "total_cost",
            "total_price",
            "profit",
            "sold_by",
            "sold_by_id",
            "sold_at",
            "added_at",
            "updated_at",
        ]
