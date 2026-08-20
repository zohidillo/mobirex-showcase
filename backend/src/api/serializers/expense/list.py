"""Expense list serializers."""

from rest_framework import serializers

import src.core.models as models


class ExpenseBranchSerializer(serializers.ModelSerializer):
    """Serialize expense branch details."""

    class Meta:
        model = models.Branch
        fields = ["id", "name", "address", "is_active"]


class ExpenseUserSerializer(serializers.ModelSerializer):
    """Serialize expense user details."""

    class Meta:
        model = models.User
        fields = ["id", "username"]


class ExpenseListSerializer(serializers.ModelSerializer):
    """Serialize expenses with template-visible fields."""

    branch = ExpenseBranchSerializer(read_only=True)
    created_by = ExpenseUserSerializer(read_only=True)
    employee = ExpenseUserSerializer(source="created_by", read_only=True)
    branch_id = serializers.IntegerField(read_only=True)
    created_by_id = serializers.IntegerField(read_only=True)
    employee_id = serializers.IntegerField(source="created_by_id", read_only=True)
    type_display = serializers.ReadOnlyField(source="get_type_display")

    class Meta:
        model = models.Expense
        fields = [
            "id",
            "branch",
            "branch_id",
            "type",
            "type_display",
            "amount",
            "note",
            "created_by",
            "created_by_id",
            "employee",
            "employee_id",
            "added_at",
            "updated_at",
        ]
