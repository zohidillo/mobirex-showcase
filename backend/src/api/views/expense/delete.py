"""Expense delete views."""

from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _

from drf_spectacular.utils import extend_schema

import src.core.models as models
from src.api.base import BaseAPIView
from src.api.schema import build_message_data_schema, build_success_response_schema
from src.api.views.expense.list import ExpenseAccessMixin
from src.services.expense import ExpenseDeleteService
from src.shared.permissions import is_owner, user_can_access_owner_branch


EXPENSE_DELETE_RESPONSE_SCHEMA = build_success_response_schema(
    "ExpenseDeleteResponse",
    build_message_data_schema("ExpenseDeleteData"),
)


class ExpenseDeleteAPIView(ExpenseAccessMixin, BaseAPIView):
    """Delete an expense via `/expenses/{id}/`."""

    def get_object(self):
        expense = get_object_or_404(
            models.Expense.objects.filter(is_deleted=False).select_related("branch", "created_by"),
            pk=self.kwargs["pk"],
        )
        user = self.request.user
        if is_owner(user):
            if not user_can_access_owner_branch(user, expense.branch):
                raise PermissionDenied(_("Sizga bu amalni bajarish mumkin emas."))
            return expense
        if expense.created_by_id != user.id:
            raise PermissionDenied(_("Sizga bu amalni bajarish mumkin emas."))
        if not (
            user.has_role("PHONE_SELLER", expense.branch)
            or user.has_role("ACCESSORY_SELLER", expense.branch)
        ):
            raise PermissionDenied(_("Sizga bu amalni bajarish mumkin emas."))
        return expense

    @extend_schema(
        tags=["Expense"],
        responses={200: EXPENSE_DELETE_RESPONSE_SCHEMA},
    )
    def delete(self, request, *args, **kwargs):
        user = request.user
        if not (
            is_owner(user)
            or user.has_role("PHONE_SELLER")
            or user.has_role("ACCESSORY_SELLER")
        ):
            raise PermissionDenied(_("Sizga bu amalni bajarish mumkin emas."))
        expense = self.get_object()
        ExpenseDeleteService.delete_expense(expense, deleted_by=user)
        return self.success({"message": _("Xarajat o'chirildi.")}, status=200)
