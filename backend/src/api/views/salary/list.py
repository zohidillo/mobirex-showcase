"""Salary list views."""

from django.core.exceptions import PermissionDenied
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from rest_framework.permissions import IsAuthenticated

from drf_spectacular.utils import OpenApiParameter, extend_schema

import src.core.models as models
from src.api.base import BaseAPIView
from src.api.schema import YEAR_MONTH_PARAMETERS, build_paginated_response_schema
from src.api.serializers.salary import SalaryListSerializer
from src.shared.filters import filter_by_month
from src.shared.permissions import get_owner_branches, is_accessory_seller, is_owner, is_phone_seller


SALARY_LIST_RESPONSE_SCHEMA = build_paginated_response_schema(
    "SalaryListResponse",
    SalaryListSerializer,
)


class SalaryAccessMixin:
    """Share salary access helpers."""

    permission_classes = [IsAuthenticated]

    def require_access(self, user):
        if not (is_owner(user) or is_phone_seller(user) or is_accessory_seller(user)):
            raise PermissionDenied(_("Sizga bu amalni bajarish mumkin emas."))


class SalaryListAPIView(SalaryAccessMixin, BaseAPIView):
    """List salaries. Owners see branches. Sellers see only own salary (current year default)."""

    def get_queryset(self):
        """Build the filtered salary queryset."""
        user = self.request.user
        self.require_access(user)

        queryset = models.Salary.objects.filter(is_deleted=False).select_related(
            "employee",
            "branch",
            "created_by",
        )

        if is_owner(user):
            owner_branches = get_owner_branches(user)
            if not owner_branches:
                return models.Salary.objects.none()
            queryset = queryset.filter(branch__in=owner_branches)

            branch_ids = [branch.id for branch in owner_branches if branch]
            branch_id = self.request.query_params.get("branch")
            if branch_id:
                try:
                    branch_id_int = int(branch_id)
                except (TypeError, ValueError):
                    branch_id_int = None
                if branch_id_int in branch_ids:
                    queryset = queryset.filter(branch_id=branch_id_int)

            employee_id = self.request.query_params.get("employee")
            if employee_id:
                queryset = queryset.filter(employee_id=employee_id)

            queryset = queryset.order_by("-added_at")
            return filter_by_month(
                queryset,
                self.request,
                field_name="added_at",
                default_to_current=True,
            )

        # Seller: see only own salaries, default to current year
        queryset = queryset.filter(employee=user).order_by("-added_at")

        year_param = self.request.query_params.get("year")
        month_param = self.request.query_params.get("month")
        try:
            year_int = int(year_param)
        except (TypeError, ValueError):
            year_int = None
        try:
            month_int = int(month_param)
        except (TypeError, ValueError):
            month_int = None

        if year_int and month_int:
            return filter_by_month(
                queryset,
                self.request,
                field_name="added_at",
                default_to_current=False,
            )
        if year_int:
            return queryset.filter(added_at__year=year_int)

        # Default: current year for sellers
        return queryset.filter(added_at__year=timezone.localdate().year)

    @extend_schema(
        tags=["Salary"],
        parameters=[
            *YEAR_MONTH_PARAMETERS,
            OpenApiParameter(name="branch", type=int, required=False),
            OpenApiParameter(name="employee", type=int, required=False),
        ],
        responses={200: SALARY_LIST_RESPONSE_SCHEMA},
    )
    def get(self, request, *args, **kwargs):
        """Return paginated salary data."""
        queryset = self.get_queryset()
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(queryset, request, view=self)
        serializer = SalaryListSerializer(page, many=True, context={"request": request})
        return paginator.get_paginated_response(serializer.data)
