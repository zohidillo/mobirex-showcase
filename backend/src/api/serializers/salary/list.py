"""Salary list serializers."""

from rest_framework import serializers

import src.core.models as models


class SalaryBranchSerializer(serializers.ModelSerializer):
    """Serialize salary branch details."""

    class Meta:
        model = models.Branch
        fields = ["id", "name", "address", "is_active"]


class SalaryUserSerializer(serializers.ModelSerializer):
    """Serialize salary user details."""

    class Meta:
        model = models.User
        fields = ["id", "username"]


class SalaryListSerializer(serializers.ModelSerializer):
    """Serialize salaries with the fields shown in web."""

    branch = SalaryBranchSerializer(read_only=True)
    employee = SalaryUserSerializer(read_only=True)
    created_by = SalaryUserSerializer(read_only=True)
    branch_id = serializers.IntegerField(read_only=True)
    employee_id = serializers.IntegerField(read_only=True)
    created_by_id = serializers.IntegerField(read_only=True)

    class Meta:
        model = models.Salary
        fields = [
            "id",
            "branch",
            "branch_id",
            "employee",
            "employee_id",
            "amount",
            "note",
            "created_by",
            "created_by_id",
            "added_at",
            "updated_at",
        ]
