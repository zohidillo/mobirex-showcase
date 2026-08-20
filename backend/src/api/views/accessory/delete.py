from django.core.exceptions import PermissionDenied, ValidationError
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _

from drf_spectacular.utils import extend_schema

import src.core.models as models
from src.api.base import BaseAPIView
from src.api.schema import build_message_data_schema, build_success_response_schema
from src.api.views.accessory.list import AccessoryAccessMixin
from src.services.accessory import AccessoryDeleteService


ACCESSORY_DELETE_RESPONSE_SCHEMA = build_success_response_schema(
    "AccessoryDeleteResponse",
    build_message_data_schema("AccessoryDeleteData"),
)


class AccessoryDeleteAPIView(AccessoryAccessMixin, BaseAPIView):
    """Delete an accessory via `/accessories/{id}/`."""

    def get_object(self):
        accessory = get_object_or_404(
            models.Accessory.objects.filter(is_deleted=False).select_related("branch", "added_by"),
            pk=self.kwargs["pk"],
        )
        user = self.request.user
        if user.has_role("ACCESSORY_SELLER", accessory.branch):
            if accessory.added_by_id != user.id:
                raise PermissionDenied(_("Sizga bu amalni bajarish mumkin emas."))
        elif user.has_role("OWNER", accessory.branch):
            pass
        else:
            raise PermissionDenied(_("Sizga bu amalni bajarish mumkin emas."))
        return accessory

    @extend_schema(
        tags=["Accessory"],
        responses={200: ACCESSORY_DELETE_RESPONSE_SCHEMA},
    )
    def delete(self, request, *args, **kwargs):
        self.require_access(request.user)
        accessory = self.get_object()
        try:
            AccessoryDeleteService.delete_accessory(accessory, deleted_by=request.user)
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        return self.success({"message": _("Aksessuar o‘chirildi.")}, status=200)

