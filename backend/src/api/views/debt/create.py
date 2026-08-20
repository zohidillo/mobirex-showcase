"""Debt create views."""

from drf_spectacular.utils import extend_schema

from src.api.base import BaseAPIView
from src.api.schema import build_success_response_schema
from src.api.serializers.debt import DebtCreateSerializer, DebtListSerializer
from src.api.views.debt.list import DebtAccessMixin


DEBT_CREATE_RESPONSE_SCHEMA = build_success_response_schema(
    "DebtCreateResponse",
    DebtListSerializer,
)


class DebtCreateAPIView(DebtAccessMixin, BaseAPIView):
    """Create debt. Only sellers allowed. Branch auto assigned."""

    @extend_schema(
        tags=["Debt"],
        request=DebtCreateSerializer,
        responses={201: DEBT_CREATE_RESPONSE_SCHEMA},
    )
    def post(self, request, *args, **kwargs):
        """Create a debt by delegating to the existing service."""
        serializer = DebtCreateSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        debt = serializer.save()
        return self.success(
            DebtListSerializer(debt, context={"request": request}).data,
            status=201,
        )
