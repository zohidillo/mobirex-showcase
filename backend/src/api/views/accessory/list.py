from django.core.exceptions import PermissionDenied
from django.utils.translation import gettext_lazy as _
from rest_framework.permissions import IsAuthenticated

from drf_spectacular.utils import OpenApiParameter, extend_schema

import src.core.models as models
from src.api.base import BaseAPIView
from src.api.schema import PAGINATION_PARAMETERS, YEAR_MONTH_PARAMETERS, build_paginated_response_schema
from src.api.serializers.accessory import AccessoryListSerializer, AccessorySaleSerializer
from src.shared.filters import filter_by_month
from src.shared.permissions import (
    can_access_branch,
    get_owner_branches,
    is_accessory_seller,
    is_owner,
)


def can_manage_accessory_branch(user, branch):
    """Return whether the user may manage accessories in the branch."""
    if user.has_role("ACCESSORY_SELLER", branch):
        return True
    return is_owner(user) and can_access_branch(user, branch)


ACCESSORY_UNSOLD_LIST_RESPONSE_SCHEMA = build_paginated_response_schema(
    "AccessoryUnsoldListResponse",
    AccessoryListSerializer,
)
ACCESSORY_SOLD_LIST_RESPONSE_SCHEMA = build_paginated_response_schema(
    "AccessorySoldListResponse",
    AccessorySaleSerializer,
)


class AccessoryAccessMixin:
    """Share accessory branch access helpers."""

    permission_classes = [IsAuthenticated]

    def require_access(self, user):
        """Ensure the user can access accessory endpoints."""
        if not (is_owner(user) or is_accessory_seller(user)):
            raise PermissionDenied(_("Ruxsat yo‘q."))

    def get_owner_branch_ids(self, user):
        """Return owner branch ids for the user."""
        return [branch.id for branch in get_owner_branches(user)]


class AccessoryUnsoldListAPIView(AccessoryAccessMixin, BaseAPIView):
    """List unsold accessories with the same filters as web."""

    def get_queryset(self):
        """Build the filtered accessory inventory queryset."""
        user = self.request.user
        self.require_access(user)

        queryset = (
            models.Accessory.objects.filter(is_deleted=False, stock__gt=0, is_month_closed=False)
            .select_related("branch", "added_by", "category")
            .order_by("-added_at")
        )

        if is_owner(user):
            branch_ids = self.get_owner_branch_ids(user)
            if not branch_ids:
                return models.Accessory.objects.none()
            queryset = queryset.filter(branch_id__in=branch_ids)
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
                queryset = queryset.filter(added_by_id=employee_id)
        else:
            branch = user.get_primary_branch("ACCESSORY_SELLER")
            if not branch:
                return models.Accessory.objects.none()
            queryset = queryset.filter(branch=branch)

        q = self.request.query_params.get("q")
        category = self.request.query_params.get("category")

        if q:
            queryset = queryset.filter(name__icontains=q)
        if category:
            queryset = queryset.filter(category_id=category)

        return queryset

    @extend_schema(
        tags=["Accessory"],
        parameters=[
            *PAGINATION_PARAMETERS,
            OpenApiParameter(name="branch", type=int, required=False),
            OpenApiParameter(name="employee", type=int, required=False),
            OpenApiParameter(name="q", type=str, required=False),
            OpenApiParameter(name="category", type=int, required=False),
        ],
        responses={200: ACCESSORY_UNSOLD_LIST_RESPONSE_SCHEMA},
    )
    def get(self, request, *args, **kwargs):
        """Return paginated accessory inventory."""
        queryset = self.get_queryset()
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(queryset, request, view=self)
        serializer = AccessoryListSerializer(page, many=True, context={"request": request})
        return paginator.get_paginated_response(serializer.data)


class AccessorySoldListAPIView(AccessoryAccessMixin, BaseAPIView):
    """List sold accessories with the same filters as web (current month default)."""

    def get_queryset(self):
        user = self.request.user
        self.require_access(user)

        queryset = (
            models.AccessorySale.objects.filter(is_deleted=False)
            .select_related(
                "branch",
                "sold_by",
                "accessory",
                "accessory__branch",
                "accessory__category",
                "accessory__added_by",
            )
            .order_by("-sold_at", "-added_at")
        )

        if is_owner(user):
            branch_ids = self.get_owner_branch_ids(user)
            if not branch_ids:
                return models.AccessorySale.objects.none()
            queryset = queryset.filter(branch_id__in=branch_ids)
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
                queryset = queryset.filter(sold_by_id=employee_id)
        else:
            branch = user.get_primary_branch("ACCESSORY_SELLER")
            if not branch:
                return models.AccessorySale.objects.none()
            queryset = queryset.filter(branch=branch)

        q = self.request.query_params.get("q")
        category = self.request.query_params.get("category")

        if q:
            queryset = queryset.filter(accessory__name__icontains=q)
        if category:
            queryset = queryset.filter(accessory__category_id=category)

        return filter_by_month(
            queryset,
            self.request,
            field_name="sold_at",
            default_to_current=True,
        )

    @extend_schema(
        tags=["Accessory"],
        parameters=[
            *YEAR_MONTH_PARAMETERS,
            OpenApiParameter(name="branch", type=int, required=False),
            OpenApiParameter(name="employee", type=int, required=False),
            OpenApiParameter(name="q", type=str, required=False),
            OpenApiParameter(name="category", type=int, required=False),
        ],
        responses={200: ACCESSORY_SOLD_LIST_RESPONSE_SCHEMA},
    )
    def get(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(queryset, request, view=self)
        serializer = AccessorySaleSerializer(page, many=True, context={"request": request})
        return paginator.get_paginated_response(serializer.data)
