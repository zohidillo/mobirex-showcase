"""Extra profit list views."""

from django.core.exceptions import PermissionDenied
from django.utils.translation import gettext_lazy as _
from rest_framework.permissions import IsAuthenticated

from drf_spectacular.utils import OpenApiParameter, extend_schema

import src.core.models as models
from src.api.base import BaseAPIView
from src.api.schema import YEAR_MONTH_PARAMETERS, build_paginated_response_schema
from src.api.serializers.extra_profit import ExtraProfitListSerializer
from src.services.extra_profit.policy import (
    filter_extra_profit_queryset_for_user,
    get_owned_branches_for_extra_profit,
)
from src.shared.filters import filter_by_month
from src.shared.permissions import is_owner, is_phone_seller


EXTRA_PROFIT_LIST_RESPONSE_SCHEMA = build_paginated_response_schema(
    "ExtraProfitListResponse",
    ExtraProfitListSerializer,
)


class ExtraProfitAccessMixin:
    """Share extra profit access helpers."""

    permission_classes = [IsAuthenticated]

    def require_view_access(self, user):
        """Ensure the user may view extra profit endpoints (owner or phone seller only)."""
        if not (is_owner(user) or is_phone_seller(user)):
            raise PermissionDenied(_("Sizga bu amalni bajarish mumkin emas."))

    def require_create_or_delete_access(self, user):
        """Ensure the user may create or delete extra profit rows (phone seller or owner)."""
        if not (is_owner(user) or is_phone_seller(user)):
            raise PermissionDenied(_("Sizga bu amalni bajarish mumkin emas."))

    def owner_branch_ids(self, user):
        """Return owner branch ids for the user."""
        return [branch.id for branch in get_owned_branches_for_extra_profit(user)]


class ExtraProfitListAPIView(ExtraProfitAccessMixin, BaseAPIView):
    """List extra profit. Filtered by month/year and branch scope."""

    def get_queryset(self):
        """Build the filtered extra profit queryset."""
        user = self.request.user
        self.require_view_access(user)

        queryset = (
            models.ExtraProfit.objects.filter(is_deleted=False)
            .select_related("branch", "created_by")
            .order_by("-added_at")
        )
        queryset = filter_extra_profit_queryset_for_user(queryset, user)

        if is_owner(user):
            branch_ids = self.owner_branch_ids(user)
            branch_id = self.request.query_params.get("branch")
            if branch_id:
                try:
                    branch_id_int = int(branch_id)
                except (TypeError, ValueError):
                    branch_id_int = None
                if branch_id_int in branch_ids:
                    queryset = queryset.filter(branch_id=branch_id_int)

        return filter_by_month(
            queryset,
            self.request,
            field_name="added_at",
            default_to_current=True,
        )

    @extend_schema(
        tags=["Extra Profit"],
        parameters=[
            *YEAR_MONTH_PARAMETERS,
            OpenApiParameter(name="branch", type=int, required=False),
        ],
        responses={200: EXTRA_PROFIT_LIST_RESPONSE_SCHEMA},
    )
    def get(self, request, *args, **kwargs):
        """Return paginated extra profit rows."""
        queryset = self.get_queryset()
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(queryset, request, view=self)
        serializer = ExtraProfitListSerializer(page, many=True, context={"request": request})
        return paginator.get_paginated_response(serializer.data)
