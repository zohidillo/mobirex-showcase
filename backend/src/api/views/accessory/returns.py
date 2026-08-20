from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _

from drf_spectacular.utils import extend_schema

import src.core.models as models
from src.api.base import BaseAPIView
from src.api.schema import build_message_data_schema, build_success_response_schema
from src.api.views.accessory.list import AccessoryAccessMixin
from src.services.accessory.returns import AccessoryReturnService


ACCESSORY_RETURN_RESPONSE_SCHEMA = build_success_response_schema(
    "AccessoryReturnResponse",
    build_message_data_schema("AccessoryReturnData"),
)


class AccessoryReturnAPIView(AccessoryAccessMixin, BaseAPIView):
    """Return a sold accessory via `/accessories/sales/{id}/return/`."""

    def get_object(self):
        return get_object_or_404(
            models.AccessorySale.objects.filter(is_deleted=False).select_related(
                "branch",
                "sold_by",
                "accessory",
                "accessory__branch",
                "accessory__category",
                "accessory__added_by",
            ),
            pk=self.kwargs["pk"],
        )

    @extend_schema(
        tags=["Accessory"],
        responses={200: ACCESSORY_RETURN_RESPONSE_SCHEMA},
    )
    def post(self, request, *args, **kwargs):
        self.require_access(request.user)
        sale = self.get_object()
        AccessoryReturnService.return_sale(sale, returned_by=request.user)
        return self.success({"message": _("Aksessuar qaytarilishi yakunlandi.")}, status=200)

