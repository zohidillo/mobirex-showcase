"""Extra profit delete views."""

from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _

from drf_spectacular.utils import extend_schema

import src.core.models as models
from src.api.base import BaseAPIView
from src.api.schema import build_message_data_schema, build_success_response_schema
from src.api.views.extra_profit.list import ExtraProfitAccessMixin
from src.services.extra_profit import ExtraProfitDeleteService
from src.services.extra_profit.policy import (
    can_delete_extra_profit,
    filter_extra_profit_queryset_for_user,
    is_current_month_extra_profit,
)
from src.shared.permissions import is_owner, is_phone_seller


EXTRA_PROFIT_DELETE_RESPONSE_SCHEMA = build_success_response_schema(
    "ExtraProfitDeleteResponse",
    build_message_data_schema("ExtraProfitDeleteData"),
)


class ExtraProfitDeleteAPIView(ExtraProfitAccessMixin, BaseAPIView):
    """Delete extra profit for the current month (owner or phone seller)."""

    def get_object(self):
        queryset = (
            models.ExtraProfit.objects.filter(is_deleted=False)
            .select_related("branch", "created_by")
            .order_by("-added_at")
        )
        queryset = filter_extra_profit_queryset_for_user(queryset, self.request.user)
        extra_profit = get_object_or_404(queryset, pk=self.kwargs["pk"])

        if not is_current_month_extra_profit(extra_profit):
            raise PermissionDenied(_("Qo'shimcha foyda faqat joriy oyda o'chirilishi mumkin."))
        if not can_delete_extra_profit(self.request.user, extra_profit):
            raise PermissionDenied(_("Sizga bu amalni bajarish mumkin emas."))
        return extra_profit

    @extend_schema(
        tags=["Extra Profit"],
        responses={200: EXTRA_PROFIT_DELETE_RESPONSE_SCHEMA},
    )
    def delete(self, request, *args, **kwargs):
        user = request.user
        if not (is_owner(user) or is_phone_seller(user)):
            raise PermissionDenied(_("Sizga bu amalni bajarish mumkin emas."))
        extra_profit = self.get_object()
        ExtraProfitDeleteService.delete_extra_profit(extra_profit, deleted_by=user)
        return self.success({"message": _("Qo'shimcha foyda o'chirildi.")}, status=200)
