"""Debt payment list/delete views."""

from datetime import date

from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _

from drf_spectacular.utils import OpenApiParameter, extend_schema

import src.core.models as models
from src.api.base import BaseAPIView
from src.api.schema import (
    YEAR_MONTH_PARAMETERS,
    build_message_data_schema,
    build_paginated_response_schema,
    build_success_response_schema,
)
from src.api.serializers.debt import DebtPaymentSerializer
from src.api.views.debt.list import DebtAccessMixin
from src.services.debt import (
    DebtPaymentDeleteService,
    filter_payments_by_debt_month,
    is_debt_in_current_month,
    get_month_window
)

from src.shared.filters import get_request_year_month
from src.shared.permissions import (
    can_access_branch,
    get_primary_seller_branch,
    get_seller_domain_for_branch,
    get_owner_branches,
    is_owner,
)

DEBT_PAYMENT_LIST_RESPONSE_SCHEMA = build_paginated_response_schema(
    "DebtPaymentListResponse",
    DebtPaymentSerializer,
)
DEBT_PAYMENT_DELETE_RESPONSE_SCHEMA = build_success_response_schema(
    "DebtPaymentDeleteResponse",
    build_message_data_schema("DebtPaymentDeleteData"),
)


class DebtPaymentListAPIView(DebtAccessMixin, BaseAPIView):
    """List debt payments filtered by debt month (default: current month)."""

    def get_selected_month_start(self, *, default_to_current=False):
        year, month = get_request_year_month(
            self.request,
            default_to_current=default_to_current,
            source=self.request.path,
        )
        if not year or not month:
            return None
        return date(year, month, 1)

    def _get_requested_debt_id(self):
        value = (
                self.request.query_params.get("debt")
                or self.request.query_params.get("debt_id")
        )
        if not value:
            return None

        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    def _has_explicit_year_month_filter(self):
        return bool(
            self.request.query_params.get("year")
            and self.request.query_params.get("month")
        )

    def _apply_payment_added_at_month_filter(self, queryset, month_start):
        if not month_start:
            return queryset

        _, _, month_start_dt, next_month_start_dt = get_month_window(month_start)
        return queryset.filter(
            added_at__gte=month_start_dt,
            added_at__lt=next_month_start_dt,
        )

    def get_queryset(self):
        user = self.request.user
        self.require_view_access(user)

        queryset = (
            models.DebtPayment.objects.filter(is_deleted=False, debt__is_deleted=False)
            .select_related("debt", "debt__branch", "debt__created_by", "paid_by")
            .order_by("-added_at", "-id")
        )

        if is_owner(user):
            branch_ids = [branch.id for branch in get_owner_branches(user)]
            if not branch_ids:
                return models.DebtPayment.objects.none()
            queryset = queryset.filter(debt__branch_id__in=branch_ids)
        else:
            branch = get_primary_seller_branch(user)
            if not branch or not can_access_branch(user, branch):
                return models.DebtPayment.objects.none()

            seller_domain = get_seller_domain_for_branch(user, branch)
            queryset = queryset.filter(debt__branch=branch)

            if seller_domain == models.Debt.DOMAIN_ACCESSORY:
                queryset = queryset.filter(debt__domain=models.Debt.DOMAIN_ACCESSORY)
            elif seller_domain == models.Debt.DOMAIN_PHONE:
                queryset = queryset.filter(
                    Q(debt__domain=models.Debt.DOMAIN_PHONE) | Q(debt__domain__isnull=True)
                )
            else:
                return models.DebtPayment.objects.none()

        debt_id = self._get_requested_debt_id()

        if debt_id:
            queryset = queryset.filter(debt_id=debt_id)
            if self._has_explicit_year_month_filter():
                month_start = self.get_selected_month_start(default_to_current=False)
                queryset = self._apply_payment_added_at_month_filter(
                    queryset,
                    month_start,
                )

            return queryset

        month_start = self.get_selected_month_start(default_to_current=True)
        return filter_payments_by_debt_month(
            queryset,
            month_start,
            default_to_current=True,
        )

    @extend_schema(
        tags=["Debt"],
        parameters=[
            *YEAR_MONTH_PARAMETERS,
        ],
        responses={200: DEBT_PAYMENT_LIST_RESPONSE_SCHEMA},
    )
    def get(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(queryset, request, view=self)
        serializer = DebtPaymentSerializer(page, many=True, context={"request": request})
        return paginator.get_paginated_response(serializer.data)


class DebtPaymentDeleteAPIView(DebtAccessMixin, BaseAPIView):
    """Delete a debt payment (owner-only, current-month only)."""

    def get_object(self):
        payment = get_object_or_404(
            models.DebtPayment.objects.filter(is_deleted=False, debt__is_deleted=False).select_related(
                "debt",
                "debt__branch",
                "debt__created_by",
            ),
            pk=self.kwargs["pk"],
        )

        user = self.request.user
        self.require_view_access(user)

        if not is_owner(user):
            raise PermissionDenied(_("Sizga bu amalni bajarish mumkin emas."))

        owner_branch_ids = {branch.id for branch in get_owner_branches(user)}
        if payment.debt.branch_id not in owner_branch_ids:
            raise PermissionDenied(_("Sizga bu amalni bajarish mumkin emas."))

        if not is_debt_in_current_month(payment.debt):
            raise PermissionDenied(_("To‘lov faqat joriy oyda o‘chirilishi mumkin."))

        return payment

    @extend_schema(
        tags=["Debt"],
        responses={200: DEBT_PAYMENT_DELETE_RESPONSE_SCHEMA},
    )
    def delete(self, request, *args, **kwargs):
        payment = self.get_object()
        DebtPaymentDeleteService.delete_payment(payment, deleted_by=request.user)
        return self.success({"message": _("To‘lov o‘chirildi.")}, status=200)
