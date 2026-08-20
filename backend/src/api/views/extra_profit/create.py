"""Extra profit create views."""

from django.core.exceptions import PermissionDenied
from django.utils.translation import gettext_lazy as _

from drf_spectacular.utils import extend_schema

from src.api.base import BaseAPIView
from src.api.schema import build_success_response_schema
from src.api.serializers.extra_profit import ExtraProfitCreateSerializer, ExtraProfitListSerializer
from src.api.views.extra_profit.list import ExtraProfitAccessMixin
from src.shared.permissions import is_phone_seller


EXTRA_PROFIT_CREATE_RESPONSE_SCHEMA = build_success_response_schema(
    "ExtraProfitCreateResponse",
    ExtraProfitListSerializer,
)


class ExtraProfitCreateAPIView(ExtraProfitAccessMixin, BaseAPIView):
    """Create extra profit. Only phone sellers are allowed."""

    @extend_schema(
        tags=["Extra Profit"],
        request=ExtraProfitCreateSerializer,
        responses={201: EXTRA_PROFIT_CREATE_RESPONSE_SCHEMA},
    )
    def post(self, request, *args, **kwargs):
        """Create extra profit through the existing service."""
        if not is_phone_seller(request.user):
            raise PermissionDenied(_("Sizga bu amalni bajarish mumkin emas."))
        serializer = ExtraProfitCreateSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        extra_profit = serializer.save()
        return self.success(
            ExtraProfitListSerializer(extra_profit, context={"request": request}).data,
            status=201,
        )
