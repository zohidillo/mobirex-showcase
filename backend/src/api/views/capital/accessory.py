"""Accessory capital views (owner only, view-only)."""

from datetime import date

from django.core.exceptions import PermissionDenied
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from rest_framework.permissions import IsAuthenticated

from drf_spectacular.utils import extend_schema

import src.core.models as models
from src.api.base import BaseAPIView
from src.api.schema import PAGINATION_PARAMETERS, build_paginated_response_schema
from src.api.serializers.capital import AccessoryCapitalSerializer
from src.shared.permissions import get_owner_branches, is_owner


ACCESSORY_CAPITAL_LIST_RESPONSE_SCHEMA = build_paginated_response_schema(
    "AccessoryCapitalListResponse",
    AccessoryCapitalSerializer,
)


class AccessoryCapitalAPIView(BaseAPIView):
    """List accessory capital rows. Owner access only. No mutations allowed."""

    permission_classes = [IsAuthenticated]

    def _require_owner(self, user):
        if not is_owner(user):
            raise PermissionDenied(_("Sizga bu amalni bajarish mumkin emas."))

    def _build_list(self, user, year, branch_id):
        """Return accessory capital sorted: current month first, then descending."""
        branches = get_owner_branches(user)
        if not branches:
            return []

        if branch_id is not None:
            branches = [b for b in branches if b.id == branch_id]
            if not branches:
                raise PermissionDenied(_("Bu filial sizga tegishli emas."))

        queryset = (
            models.AccessoryCapital.objects.filter(
                branch__in=branches,
                month__year=year,
                is_deleted=False,
            )
            .select_related("branch")
        )

        today = timezone.localdate()
        current_month_start = today.replace(day=1)
        items = list(queryset)

        def sort_key(item):
            branch_name = (item.branch.name or "").lower() if item.branch else ""
            is_current = item.month == current_month_start
            return (branch_name, 0 if is_current else 1, -item.month.toordinal())

        items.sort(key=sort_key)
        return items

    @extend_schema(
        tags=["Capital"],
        parameters=PAGINATION_PARAMETERS,
        responses={200: ACCESSORY_CAPITAL_LIST_RESPONSE_SCHEMA},
    )
    def get(self, request, *args, **kwargs):
        """Return paginated accessory capital rows for the current year (owner only)."""
        user = request.user
        self._require_owner(user)

        today = timezone.localdate()
        try:
            year = int(request.query_params.get("year", today.year))
        except (ValueError, TypeError):
            year = today.year

        branch_id = request.query_params.get("branch")
        if branch_id is not None:
            try:
                branch_id = int(branch_id)
            except (ValueError, TypeError):
                return self.error(_("Noto'g'ri filial id."), status=400)

        items = self._build_list(user, year, branch_id)
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(items, request, view=self)
        serializer = AccessoryCapitalSerializer(page, many=True, context={"request": request})
        return paginator.get_paginated_response(serializer.data)
