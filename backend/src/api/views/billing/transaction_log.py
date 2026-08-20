"""Transaction log view."""

from rest_framework.permissions import IsAuthenticated

from drf_spectacular.utils import OpenApiParameter, extend_schema

import src.core.models as models
from src.api.base import BaseAPIView
from src.api.schema import YEAR_MONTH_RANGE_PARAMETERS, build_paginated_response_schema
from src.api.serializers.billing import TransactionLogListSerializer
from src.shared.filters import (
    apply_datetime_range,
    filter_by_month,
    parse_date_input,
)
from src.shared.permissions import is_superuser


TRANSACTION_LOG_LIST_RESPONSE_SCHEMA = build_paginated_response_schema(
    "TransactionLogListResponse",
    TransactionLogListSerializer,
)


class TransactionLogListAPIView(BaseAPIView):
    """List transaction logs. Users see own logs. Cashier and admin see all."""

    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Return the filtered transaction-log queryset."""
        user = self.request.user
        queryset = (
            models.TransactionLog.objects.filter(is_deleted=False)
            .select_related("user")
            .order_by("-charge_date", "-id")
        )

        is_staff_viewer = is_superuser(user) or user.is_cashier
        user_id = self.request.query_params.get("user")
        transaction_type = self.request.query_params.get("transaction_type") or self.request.query_params.get(
            "type"
        )
        from_date = parse_date_input(self.request.query_params.get("from_date"))
        to_date = parse_date_input(self.request.query_params.get("to_date"))

        if is_staff_viewer:
            if user_id:
                queryset = queryset.filter(user_id=user_id)
        else:
            queryset = queryset.filter(user=user)

        if transaction_type:
            queryset = queryset.filter(type=transaction_type)
        queryset = filter_by_month(
            queryset,
            self.request,
            field_name="charge_date",
        )
        return apply_datetime_range(
            queryset,
            field_name="charge_date",
            from_date=from_date,
            to_date=to_date,
        )

    @extend_schema(
        tags=["Billing"],
        parameters=[
            *YEAR_MONTH_RANGE_PARAMETERS,
            OpenApiParameter(name="user", type=int, required=False),
            OpenApiParameter(name="transaction_type", type=str, required=False),
            OpenApiParameter(
                name="type",
                type=str,
                required=False,
                description="Alias for transaction_type.",
            ),
        ],
        responses={200: TRANSACTION_LOG_LIST_RESPONSE_SCHEMA},
    )
    def get(self, request, *args, **kwargs):
        """Return paginated transaction-log data."""
        queryset = self.get_queryset()
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(queryset, request, view=self)
        serializer = TransactionLogListSerializer(page, many=True, context={"request": request})
        return paginator.get_paginated_response(serializer.data)
