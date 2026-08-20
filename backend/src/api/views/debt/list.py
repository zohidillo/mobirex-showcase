"""Debt list views."""

from datetime import date

from django.core.exceptions import PermissionDenied
from django.db.models import Prefetch, Q
from django.utils.translation import gettext_lazy as _
from rest_framework.permissions import IsAuthenticated

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema

import src.core.models as models
from src.api.base import BaseAPIView
from src.api.schema import YEAR_MONTH_PARAMETERS, build_paginated_response_schema
from src.api.serializers.debt import DebtClosedListSerializer, DebtListSerializer
from src.services.debt import (
    filter_debts_for_month,
    get_closed_debts_by_month,
    get_closed_debts_queryset,
    get_month_window,
    is_current_month,
)
from src.shared.filters import get_request_year_month
from src.shared.permissions import (
    can_access_branch,
    get_seller_domain_for_branch,
    get_owner_branches,
    get_primary_seller_branch,
    is_accessory_seller,
    is_owner,
    is_phone_seller,
    user_matches_debt_domain,
)


HISTORY_MODE_PARAMETER = OpenApiParameter(
    name="history_mode",
    type=OpenApiTypes.STR,
    required=False,
    description="Payment history mode: selected (default) or full.",
)

DEBT_LIST_RESPONSE_SCHEMA = build_paginated_response_schema(
    "DebtListResponse",
    DebtListSerializer,
)

CLOSED_DEBT_LIST_RESPONSE_SCHEMA = build_paginated_response_schema(
    "ClosedDebtListResponse",
    DebtClosedListSerializer,
)


class DebtAccessMixin:
    """Share debt access helpers for list and pay views."""

    permission_classes = [IsAuthenticated]

    def require_view_access(self, user):
        """Ensure the user may view debts."""
        if not (is_owner(user) or is_phone_seller(user) or is_accessory_seller(user)):
            raise PermissionDenied(_("Sizga bu amalni bajarish mumkin emas."))

    def _get_request_params(self):
        return getattr(self.request, "query_params", {})

    def get_selected_month_start(self, *, default_to_current=False):
        year, month = get_request_year_month(
            self.request,
            default_to_current=default_to_current,
            source=self.request.path,
        )
        if not year or not month:
            return None
        return date(year, month, 1)

    def get_history_mode(self):
        mode = (self._get_request_params().get("history_mode") or "selected").strip().lower()
        return "full" if mode == "full" else "selected"

    def get_payment_prefetch(self):
        """Prefetch active payment history in template order."""
        selected_month_start = self.get_selected_month_start(default_to_current=True)
        payments_qs = (
            models.DebtPayment.objects.filter(is_deleted=False)
            .select_related("paid_by")
            .order_by("added_at", "id")
        )
        if self.get_history_mode() == "selected" and selected_month_start:
            _, _, _, next_month_start_dt = get_month_window(selected_month_start)
            payments_qs = payments_qs.filter(added_at__lt=next_month_start_dt)

        return Prefetch(
            "payments",
            queryset=payments_qs,
            to_attr="prefetched_payments",
        )

    def get_base_queryset(self):
        """Return the base debt queryset with related objects."""
        return (
            models.Debt.objects.filter(is_deleted=False)
            .select_related("branch", "created_by")
            .prefetch_related(self.get_payment_prefetch())
            .order_by("-added_at")
        )

    def get_owner_branch_ids(self, user):
        """Return accessible owner branch ids."""
        return [branch.id for branch in get_owner_branches(user)]

    def get_seller_branch(self, user):
        """Return the seller branch when the user has valid seller access."""
        branch = get_primary_seller_branch(user)
        if not branch or not can_access_branch(user, branch):
            return None
        return branch

    def _apply_owner_scope_filters(
        self,
        queryset,
        *,
        branch_field="branch_id",
        created_by_field="created_by_id",
    ):
        user = self.request.user
        if not is_owner(user):
            return queryset

        branch_ids = self.get_owner_branch_ids(user)
        if not branch_ids:
            return queryset.none()

        branch_id = self._get_request_params().get("branch")
        if branch_id:
            try:
                branch_id_int = int(branch_id)
            except (TypeError, ValueError):
                branch_id_int = None
            if branch_id_int in branch_ids:
                queryset = queryset.filter(**{branch_field: branch_id_int})

        created_by = self._get_request_params().get("created_by")
        if created_by:
            queryset = queryset.filter(**{created_by_field: created_by})

        return queryset

    def _apply_common_filters(self, queryset):
        debt_type = self._get_request_params().get("type")
        domain = self._get_request_params().get("domain")
        q = (self._get_request_params().get("q") or "").strip()
        if debt_type:
            queryset = queryset.filter(direction=debt_type)
        if domain and is_owner(self.request.user):
            queryset = queryset.filter(domain=domain)
        if q:
            queryset = queryset.filter(f_name__icontains=q)
        return queryset

    def get_accessible_debts(self, month_start=None, *, default_to_current=False):
        """Return debts visible to the current user."""
        user = self.request.user
        queryset = self.get_base_queryset()

        if is_owner(user):
            branch_ids = self.get_owner_branch_ids(user)
            if not branch_ids:
                return models.Debt.objects.none()
            queryset = queryset.filter(branch_id__in=branch_ids)
        else:
            branch = self.get_seller_branch(user)
            if not branch:
                return models.Debt.objects.none()
            queryset = queryset.filter(branch=branch)
            seller_domain = get_seller_domain_for_branch(user, branch)
            if seller_domain == models.Debt.DOMAIN_ACCESSORY:
                queryset = queryset.filter(domain=models.Debt.DOMAIN_ACCESSORY)
            elif seller_domain == models.Debt.DOMAIN_PHONE:
                queryset = queryset.filter(Q(domain=models.Debt.DOMAIN_PHONE) | Q(domain__isnull=True))
            else:
                return models.Debt.objects.none()

        return filter_debts_for_month(
            queryset,
            month_start,
            default_to_current=default_to_current,
        )

    def can_view_or_pay_debt(self, user, debt):
        """Check whether the user may view or pay the debt."""
        if is_owner(user):
            return debt.branch_id in set(self.get_owner_branch_ids(user))

        branch = self.get_seller_branch(user)
        if not branch:
            return False
        return (
            branch.id == debt.branch_id
            and user_matches_debt_domain(user, debt)
        )

    def can_delete_debt(self, user, debt):
        """Check whether the user may delete the debt."""
        if is_owner(user):
            return debt.branch_id in set(self.get_owner_branch_ids(user))

        branch = self.get_seller_branch(user)
        if not branch:
            return False
        return (
            branch.id == debt.branch_id
            and debt.created_by_id == user.id
            and user_matches_debt_domain(user, debt)
        )


class DebtListAPIView(DebtAccessMixin, BaseAPIView):
    """List open debts for the selected debt month."""

    def get_queryset(self):
        user = self.request.user
        self.require_view_access(user)

        selected_month_start = self.get_selected_month_start(default_to_current=True)
        queryset = self.get_accessible_debts(
            selected_month_start,
            default_to_current=True,
        ).filter(remaining_amount__gt=0)
        queryset = self._apply_owner_scope_filters(queryset)
        queryset = self._apply_common_filters(queryset)
        return queryset

    @extend_schema(
        tags=["Debt"],
        parameters=[
            *YEAR_MONTH_PARAMETERS,
            HISTORY_MODE_PARAMETER,
            OpenApiParameter(name="branch", type=int, required=False),
            OpenApiParameter(name="created_by", type=int, required=False),
            OpenApiParameter(name="domain", type=str, required=False),
            OpenApiParameter(name="type", type=str, required=False),
            OpenApiParameter(name="q", type=str, required=False),
        ],
        responses={200: DEBT_LIST_RESPONSE_SCHEMA},
    )
    def get(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(queryset, request, view=self)
        serializer = DebtListSerializer(page, many=True, context={"request": request})
        return paginator.get_paginated_response(serializer.data)


class ClosedDebtListAPIView(DebtAccessMixin, BaseAPIView):
    """List fully paid debts for the selected debt month."""

    def get_queryset(self):
        user = self.request.user
        self.require_view_access(user)
        selected_month_start = self.get_selected_month_start(default_to_current=True)

        accessible_debts = self.get_accessible_debts()
        if selected_month_start:
            queryset = get_closed_debts_by_month(
                selected_month_start,
                queryset=accessible_debts,
            )
        else:
            queryset = get_closed_debts_queryset(queryset=accessible_debts)
        queryset = self._apply_owner_scope_filters(queryset)
        queryset = self._apply_common_filters(queryset)
        return queryset

    @extend_schema(
        tags=["Debt"],
        parameters=[
            *YEAR_MONTH_PARAMETERS,
            HISTORY_MODE_PARAMETER,
            OpenApiParameter(name="branch", type=int, required=False),
            OpenApiParameter(name="created_by", type=int, required=False),
            OpenApiParameter(name="domain", type=str, required=False),
            OpenApiParameter(name="type", type=str, required=False),
            OpenApiParameter(name="q", type=str, required=False),
        ],
        responses={200: CLOSED_DEBT_LIST_RESPONSE_SCHEMA},
    )
    def get(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(queryset, request, view=self)
        serializer = DebtClosedListSerializer(page, many=True, context={"request": request})
        return paginator.get_paginated_response(serializer.data)
