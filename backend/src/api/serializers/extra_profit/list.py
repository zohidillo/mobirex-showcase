"""Extra profit list serializers."""

from rest_framework import serializers

import src.core.models as models


class ExtraProfitBranchSerializer(serializers.ModelSerializer):
    """Serialize extra profit branch details."""

    class Meta:
        model = models.Branch
        fields = ["id", "name", "address", "is_active"]


class ExtraProfitUserSerializer(serializers.ModelSerializer):
    """Serialize extra profit user details."""

    class Meta:
        model = models.User
        fields = ["id", "username"]


class ExtraProfitListSerializer(serializers.ModelSerializer):
    """Serialize extra profit rows shown in web."""

    branch = ExtraProfitBranchSerializer(read_only=True)
    created_by = ExtraProfitUserSerializer(read_only=True)
    branch_id = serializers.IntegerField(read_only=True)
    created_by_id = serializers.IntegerField(read_only=True)

    class Meta:
        model = models.ExtraProfit
        fields = [
            "id",
            "amount",
            "note",
            "branch",
            "branch_id",
            "created_by",
            "created_by_id",
            "added_at",
            "updated_at",
        ]
