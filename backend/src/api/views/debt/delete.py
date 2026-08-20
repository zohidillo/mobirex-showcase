"""Debt delete view."""

from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _

from drf_spectacular.utils import extend_schema

import src.core.models as models
from src.api.base import BaseAPIView
from src.api.schema import build_message_data_schema, build_success_response_schema
from src.api.views.debt.list import DebtAccessMixin
from src.services.debt import DebtDeleteService, is_debt_in_current_month


DEBT_DELETE_RESPONSE_SCHEMA = build_success_response_schema(
    "DebtDeleteResponse",
    build_message_data_schema("DebtDeleteData"),
)


class DebtDeleteAPIView(DebtAccessMixin, BaseAPIView):
    """Delete a debt (current-month only) when access rules allow it."""

    def get_object(self):
        debt = get_object_or_404(
            models.Debt.objects.filter(is_deleted=False).select_related("branch", "created_by"),
            pk=self.kwargs["pk"],
        )

        user = self.request.user
        self.require_view_access(user)
        if not self.can_delete_debt(user, debt):
            raise PermissionDenied(_("Sizga bu amalni bajarish mumkin emas."))
        if not is_debt_in_current_month(debt):
            raise PermissionDenied(_("Qarz faqat joriy oyda o‘chirilishi mumkin."))
        return debt

    @extend_schema(
        tags=["Debt"],
        responses={200: DEBT_DELETE_RESPONSE_SCHEMA},
    )
    def delete(self, request, *args, **kwargs):
        debt = self.get_object()
        DebtDeleteService.delete_debt(debt, deleted_by=request.user)
        return self.success({"message": _("Qarz o‘chirildi.")}, status=200)
