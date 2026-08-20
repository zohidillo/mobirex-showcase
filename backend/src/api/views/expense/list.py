"""Expense list views."""

from decimal import Decimal

from django.core.exceptions import PermissionDenied
from django.db.models import Q, Sum
from django.utils.translation import gettext_lazy as _
from rest_framework.permissions import IsAuthenticated
from rest_framework import serializers

from drf_spectacular.utils import OpenApiParameter, extend_schema

import src.core.models as models
from src.api.base import BaseAPIView
from src.api.schema import YEAR_MONTH_PARAMETERS, build_paginated_response_schema
from src.api.serializers.expense import ExpenseListSerializer
from src.shared.filters import filter_by_month
from src.shared.permissions import get_owner_branches, is_accessory_seller, is_owner, is_phone_seller


EXPENSE_LIST_RESPONSE_SCHEMA = build_paginated_response_schema(
    "ExpenseListResponse",
    ExpenseListSerializer,
    extra_fields={
        "total_amount": serializers.CharField(),
    },
)


class ExpenseAccessMixin:
    """Share expense access helpers."""

    permission_classes = [IsAuthenticated]

    def require_view_access(self, user):
        """Ensure the user may list expense endpoints."""
        if not (is_owner(user) or is_phone_seller(user) or is_accessory_seller(user)):
            raise PermissionDenied(_("Sizga bu amalni bajarish mumkin emas."))

    def require_seller_access(self, user):
        """Ensure the user may create expenses (sellers only)."""
        if is_owner(user) or not (is_phone_seller(user) or is_accessory_seller(user)):
            raise PermissionDenied(_("Sizga bu amalni bajarish mumkin emas."))


def _get_domain_seller_ids(branch, role):
    """Return user IDs with the given seller role in the branch."""
    return set(
        models.BranchUser.objects.filter(
            branch=branch,
            role=role,
            is_deleted=False,
        ).values_list("user_id", flat=True)
    )


class ExpenseListAPIView(ExpenseAccessMixin, BaseAPIView):
    """List expenses. Filtered by month/year. Sellers see same branch/domain expenses."""

    def get_queryset(self):
        """Build the filtered expense queryset."""
        user = self.request.user
        self.require_view_access(user)

        queryset = (
            models.Expense.objects.filter(is_deleted=False)
            .select_related("branch", "created_by")
            .order_by("-added_at")
        )

        if is_owner(user):
            branches = get_owner_branches(user)
            branch_ids = [branch.id for branch in branches if branch]
            if not branch_ids:
                return models.Expense.objects.none()
            queryset = queryset.filter(branch_id__in=branch_ids)

            branch_id = self.request.query_params.get("branch")
            if branch_id:
                try:
                    branch_id_int = int(branch_id)
                except (TypeError, ValueError):
                    branch_id_int = None
                if branch_id_int in branch_ids:
                    queryset = queryset.filter(branch_id=branch_id_int)

            employee_id = self.request.query_params.get("employee") or self.request.query_params.get(
                "created_by"
            )
            if employee_id:
                queryset = queryset.filter(created_by_id=employee_id)

        elif is_phone_seller(user):
            branch = user.get_primary_branch("PHONE_SELLER")
            if not branch:
                return models.Expense.objects.none()
            seller_ids = _get_domain_seller_ids(branch, models.BranchUser.ROLE_PHONE_SELLER)
            queryset = queryset.filter(
                Q(branch=branch, capital_type=models.Expense.CAPITAL_TYPE_PHONE)
                | Q(branch=branch, capital_type=None, created_by_id__in=seller_ids)
            )

        elif is_accessory_seller(user):
            branch = user.get_primary_branch("ACCESSORY_SELLER")
            if not branch:
                return models.Expense.objects.none()
            seller_ids = _get_domain_seller_ids(branch, models.BranchUser.ROLE_ACCESSORY_SELLER)
            queryset = queryset.filter(
                Q(branch=branch, capital_type=models.Expense.CAPITAL_TYPE_ACCESSORY)
                | Q(branch=branch, capital_type=None, created_by_id__in=seller_ids)
            )

        else:
            return models.Expense.objects.none()

        expense_type = self.request.query_params.get("type")
        if expense_type:
            queryset = queryset.filter(type=expense_type)

        return filter_by_month(
            queryset,
            self.request,
            field_name="added_at",
            default_to_current=True,
        )

    def get_total_amount(self, queryset):
        """Return the total amount for the filtered queryset."""
        total = queryset.aggregate(total=Sum("amount"))["total"] or Decimal("0")
        return f"{total:.2f}"

    @extend_schema(
        tags=["Expense"],
        parameters=[
            *YEAR_MONTH_PARAMETERS,
            OpenApiParameter(name="branch", type=int, required=False),
            OpenApiParameter(name="employee", type=int, required=False),
            OpenApiParameter(name="type", type=str, required=False),
        ],
        responses={200: EXPENSE_LIST_RESPONSE_SCHEMA},
    )
    def get(self, request, *args, **kwargs):
        """Return paginated expense data and filtered total."""
        queryset = self.get_queryset()
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(queryset, request, view=self)
        serializer = ExpenseListSerializer(page, many=True, context={"request": request})
        return paginator.get_paginated_response(
            serializer.data,
            extra_data={"total_amount": self.get_total_amount(queryset)},
        )
