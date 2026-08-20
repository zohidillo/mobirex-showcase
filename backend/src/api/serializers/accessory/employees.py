from rest_framework import serializers

import src.core.models as models


class AccessoryEmployeeBranchSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Branch
        fields = ["id", "name"]


class AccessoryEmployeeSerializer(serializers.ModelSerializer):
    """Serialize owner employees for mobile filters."""

    id = serializers.IntegerField(source="user_id", read_only=True)
    full_name = serializers.SerializerMethodField()
    branch = AccessoryEmployeeBranchSerializer(read_only=True)
    branch_id = serializers.IntegerField(read_only=True)

    class Meta:
        model = models.BranchUser
        fields = ["id", "full_name", "role", "branch", "branch_id"]

    def get_full_name(self, obj):
        user = getattr(obj, "user", None)
        if not user:
            return ""
        full_name = (user.get_full_name() or "").strip()
        return full_name or user.get_username()

