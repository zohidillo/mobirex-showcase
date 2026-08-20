from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _

from drf_spectacular.utils import extend_schema

import src.core.models as models
from src.api.base import BaseAPIView
from src.api.schema import build_success_response_schema
from src.api.serializers.accessory import AccessorySaleSerializer, AccessorySellSerializer
from src.api.views.accessory.list import AccessoryAccessMixin, can_manage_accessory_branch
from src.services.accessory import AccessorySellService


ACCESSORY_SELL_RESPONSE_SCHEMA = build_success_response_schema(
    "AccessorySellResponse",
    AccessorySaleSerializer,
)


class AccessorySellAPIView(AccessoryAccessMixin, BaseAPIView):
    """Sell accessories with the same branch checks as web."""

    def get_object(self):
        """Return the target accessory when the user has access."""
        accessory = get_object_or_404(
            models.Accessory.objects.select_related("branch", "added_by", "category"),
            pk=self.kwargs["pk"],
            is_deleted=False,
        )
        if not can_manage_accessory_branch(self.request.user, accessory.branch):
            raise PermissionDenied(_("Sizga bu amalni bajarish mumkin emas."))
        return accessory

    @extend_schema(
        tags=["Accessory"],
        request=AccessorySellSerializer,
        responses={200: ACCESSORY_SELL_RESPONSE_SCHEMA},
    )
    def post(self, request, *args, **kwargs):
        """Sell an accessory and return the created sale record."""
        accessory = self.get_object()
        serializer = AccessorySellSerializer(
            data=request.data,
            context={"request": request, "accessory": accessory},
        )
        serializer.is_valid(raise_exception=True)
        sale = AccessorySellService.sell_accessory(
            accessory,
            quantity=serializer.validated_data["quantity"],
            total_price=serializer.validated_data["total_price"],
            sold_by=request.user,
        )
        return self.success(
            AccessorySaleSerializer(sale, context={"request": request}).data,
            status=200,
        )
