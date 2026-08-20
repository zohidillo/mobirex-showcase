"""Phone capital views (owner only)."""

from datetime import date
from decimal import Decimal
from types import SimpleNamespace

from django.core.exceptions import PermissionDenied
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from rest_framework.permissions import IsAuthenticated

from drf_spectacular.utils import extend_schema

import src.core.models as models
from src.api.base import BaseAPIView
from src.api.schema import PAGINATION_PARAMETERS, build_paginated_response_schema
from src.api.serializers.capital import (
    PhoneCapitalCreateSerializer,
    PhoneCapitalResetSerializer,
    PhoneCapitalSerializer,
)
from src.services.capital import PhoneCapitalService
from src.shared.permissions import get_owner_branches, is_owner, user_can_access_owner_branch


PHONE_CAPITAL_LIST_RESPONSE_SCHEMA = build_paginated_response_schema(
    "PhoneCapitalListResponse",
    PhoneCapitalSerializer,
)


def _sort_key(item, current_month_start):
    """Sort phone capital rows: by branch name, then current month first, then descending month."""
    branch_name = (item.branch.name or "").lower() if getattr(item, "branch", None) else ""
    is_current = getattr(item, "month", None) == current_month_start
    month_ord = item.month.toordinal() if getattr(item, "month", None) else date.min.toordinal()
    return (branch_name, 0 if is_current else 1, -month_ord)


class PhoneCapitalAPIView(BaseAPIView):
    """List or invest phone capital. Owner access only."""

    permission_classes = [IsAuthenticated]

    def _require_owner(self, user):
        if not is_owner(user):
            raise PermissionDenied(_("Sizga bu amalni bajarish mumkin emas."))

    def _build_list(self, user, year, branch_id):
        """Return sorted phone capital items with current-month placeholders."""
        branches = get_owner_branches(user)
        if not branches:
            return []

        if branch_id is not None:
            branches = [b for b in branches if b.id == branch_id]
            if not branches:
                raise PermissionDenied(_("Bu filial sizga tegishli emas."))

        queryset = (
            models.PhoneCapital.objects.filter(
                branch__in=branches,
                month__year=year,
                is_deleted=False,
            )
            .select_related("branch")
        )

        today = timezone.localdate()
        current_month_start = today.replace(day=1)
        items = list(queryset)

        if year == today.year:
            existing_branch_ids = {c.branch_id for c in items if c.month == current_month_start}
            for branch in branches:
                if branch.id not in existing_branch_ids:
                    items.append(
                        SimpleNamespace(
                            id=None,
                            branch=branch,
                            branch_id=branch.id,
                            month=current_month_start,
                            invested_amount=Decimal("0.00"),
                            current_balance=Decimal("0.00"),
                            is_placeholder=True,
                            added_at=None,
                            updated_at=None,
                        )
                    )

        items.sort(key=lambda item: _sort_key(item, current_month_start))
        return items

    @extend_schema(
        tags=["Capital"],
        parameters=PAGINATION_PARAMETERS,
        responses={200: PHONE_CAPITAL_LIST_RESPONSE_SCHEMA},
    )
    def get(self, request, *args, **kwargs):
        """Return paginated phone capital rows for the current year (owner only)."""
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
        serializer = PhoneCapitalSerializer(page, many=True, context={"request": request})
        return paginator.get_paginated_response(serializer.data)

    @extend_schema(tags=["Capital"])
    def post(self, request, *args, **kwargs):
        """Add investment to current-month PhoneCapital (owner only)."""
        user = request.user
        self._require_owner(user)

        serializer = PhoneCapitalCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        branch_id = serializer.validated_data["branch"]
        amount = serializer.validated_data["amount"]

        if not user_can_access_owner_branch(user, branch_id):
            raise PermissionDenied(_("Bu filial sizga tegishli emas."))

        capital = PhoneCapitalService.add_investment(user, branch_id, amount)
        data = PhoneCapitalSerializer(capital, context={"request": request}).data
        return self.success(data, status=201)


class PhoneCapitalResetAPIView(BaseAPIView):
    """Reset current-month PhoneCapital invested_amount (owner only)."""

    permission_classes = [IsAuthenticated]

    @extend_schema(tags=["Capital"])
    def post(self, request, *args, **kwargs):
        """Reset current-month PhoneCapital: invested_amount=0, balance -= old invested."""
        user = request.user
        if not is_owner(user):
            raise PermissionDenied(_("Sizga bu amalni bajarish mumkin emas."))

        serializer = PhoneCapitalResetSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        branch_id = serializer.validated_data["branch"]

        if not user_can_access_owner_branch(user, branch_id):
            raise PermissionDenied(_("Bu filial sizga tegishli emas."))

        capital = PhoneCapitalService.reset_current_month(user, branch_id)
        data = PhoneCapitalSerializer(capital, context={"request": request}).data
        return self.success(data)
