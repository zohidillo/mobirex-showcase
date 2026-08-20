"""Salary create serializers."""

from django.core.exceptions import PermissionDenied
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

import src.core.models as models
from src.services.salary import SalaryCreateService
from src.shared.permissions import get_owner_branch_ids, is_owner
from src.shared.validators import validate_positive_amount

SELLER_ROLES = [
    models.BranchUser.ROLE_PHONE_SELLER,
    models.BranchUser.ROLE_ACCESSORY_SELLER,
]


class SalaryCreateSerializer(serializers.ModelSerializer):
    """Create salaries with the same owner flow as web."""

    employee = serializers.PrimaryKeyRelatedField(
        queryset=models.User.objects.filter(is_deleted=False),
    )

    class Meta:
        model = models.Salary
        fields = [
            "employee",
            "amount",
            "note",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get("request")
        if request and getattr(request.user, "is_authenticated", False) and is_owner(request.user):
            owner_branch_ids = get_owner_branch_ids(request.user)
            seller_user_ids = set(
                models.BranchUser.objects.filter(
                    branch_id__in=owner_branch_ids,
                    role__in=SELLER_ROLES,
                    is_deleted=False,
                ).values_list("user_id", flat=True)
            )
            self.fields["employee"].queryset = models.User.objects.filter(
                id__in=seller_user_ids, is_deleted=False
            )

    def validate_amount(self, value):
        """Validate that the amount is positive."""
        return validate_positive_amount(value)

    def validate(self, attrs):
        """Validate that the owner can pay the selected employee."""
        user = self.context["request"].user
        if not is_owner(user):
            raise PermissionDenied(_("Sizga bu amalni bajarish mumkin emas."))

        employee = attrs.get("employee")
        if employee is not None and getattr(employee, "is_deleted", False):
            raise PermissionDenied(_("Sizga bu amalni bajarish mumkin emas."))

        branch_user = (
            models.BranchUser.objects.filter(
                user=employee,
                branch_id__in=get_owner_branch_ids(user),
                role__in=SELLER_ROLES,
                is_deleted=False,
            )
            .select_related("branch")
            .order_by("-added_at")
            .first()
        )
        if not branch_user:
            raise PermissionDenied(_("Sizga bu amalni bajarish mumkin emas."))

        self._branch_user = branch_user
        return attrs

    def create(self, validated_data):
        """Create a salary through the existing service."""
        data = dict(validated_data)
        data["branch"] = self._branch_user.branch
        return SalaryCreateService.create_salary(data, created_by=self.context["request"].user)
