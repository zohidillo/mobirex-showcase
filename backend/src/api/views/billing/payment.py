"""Billing payment views."""

from django.core.exceptions import PermissionDenied
from django.utils.translation import gettext_lazy as _
from rest_framework.permissions import IsAuthenticated

from drf_spectacular.utils import OpenApiParameter, extend_schema

import src.core.models as models
from src.api.base import BaseAPIView
from src.api.schema import (
    YEAR_MONTH_RANGE_PARAMETERS,
    build_paginated_response_schema,
    build_success_response_schema,
)
from src.api.serializers.billing import BillingPaymentCreateSerializer, BillingPaymentListSerializer
from src.shared.filters import (
    apply_datetime_range,
    filter_by_month,
    parse_date_input,
)
from src.shared.permissions import is_superuser


class BillingPaymentAccessMixin:
    """Limit payment endpoints to cashier and superadmin users."""

    permission_classes = [IsAuthenticated]

    def require_access(self, user):
        """Ensure the user can access cashier payment endpoints."""
        if not (is_superuser(user) or user.is_cashier):
            raise PermissionDenied(_("Sizga bu amalni bajarish mumkin emas."))


BILLING_PAYMENT_LIST_RESPONSE_SCHEMA = build_paginated_response_schema(
    "BillingPaymentListResponse",
    BillingPaymentListSerializer,
)
BILLING_PAYMENT_CREATE_RESPONSE_SCHEMA = build_success_response_schema(
    "BillingPaymentCreateResponse",
    BillingPaymentListSerializer,
)


class BillingPaymentListAPIView(BillingPaymentAccessMixin, BaseAPIView):
    """List billing payments. Cashier and admin only."""

    def get_queryset(self):
        """Return the filtered payment queryset."""
        self.require_access(self.request.user)
        queryset = (
            models.Payment.objects.filter(is_deleted=False)
            .select_related("user", "added_by")
            .order_by("-added_at")
        )

        user_id = self.request.query_params.get("user")
        payment_type = self.request.query_params.get("payment_type")
        from_date = parse_date_input(self.request.query_params.get("from_date"))
        to_date = parse_date_input(self.request.query_params.get("to_date"))

        if user_id:
            queryset = queryset.filter(user_id=user_id)
        if payment_type:
            queryset = queryset.filter(payment_type=payment_type)
        queryset = filter_by_month(
            queryset,
            self.request,
            field_name="added_at",
        )
        return apply_datetime_range(
            queryset,
            field_name="added_at",
            from_date=from_date,
            to_date=to_date,
        )

    @extend_schema(
        tags=["Billing"],
        parameters=[
            *YEAR_MONTH_RANGE_PARAMETERS,
            OpenApiParameter(name="user", type=int, required=False),
            OpenApiParameter(name="payment_type", type=str, required=False),
        ],
        responses={200: BILLING_PAYMENT_LIST_RESPONSE_SCHEMA},
    )
    def get(self, request, *args, **kwargs):
        """Return paginated payment data."""
        queryset = self.get_queryset()
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(queryset, request, view=self)
        serializer = BillingPaymentListSerializer(page, many=True, context={"request": request})
        return paginator.get_paginated_response(serializer.data)


class BillingPaymentCreateAPIView(BillingPaymentAccessMixin, BaseAPIView):
    """Create billing payments. Cashier and admin only."""

    @extend_schema(
        tags=["Billing"],
        request=BillingPaymentCreateSerializer,
        responses={201: BILLING_PAYMENT_CREATE_RESPONSE_SCHEMA},
    )
    def post(self, request, *args, **kwargs):
        """Create a payment through the existing billing service."""
        self.require_access(request.user)
        serializer = BillingPaymentCreateSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        payment = serializer.save()
        return self.success(
            BillingPaymentListSerializer(payment, context={"request": request}).data,
            status=201,
        )
