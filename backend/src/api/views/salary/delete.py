"""Salary delete views."""

from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _

from drf_spectacular.utils import extend_schema

import src.core.models as models
from src.api.base import BaseAPIView
from src.api.schema import build_message_data_schema, build_success_response_schema
from src.api.views.salary.list import SalaryAccessMixin
from src.services.salary import SalaryDeleteService
from src.shared.permissions import user_can_access_owner_branch


SALARY_DELETE_RESPONSE_SCHEMA = build_success_response_schema(
    "SalaryDeleteResponse",
    build_message_data_schema("SalaryDeleteData"),
)


class SalaryDeleteAPIView(SalaryAccessMixin, BaseAPIView):
    """Delete salary. Only owners for own branches."""

    def get_object(self):
        salary = get_object_or_404(
            models.Salary.objects.filter(is_deleted=False).select_related("branch", "employee"),
            pk=self.kwargs["pk"],
        )
        if not user_can_access_owner_branch(self.request.user, salary.branch):
            raise PermissionDenied(_("Sizga bu amalni bajarish mumkin emas."))
        return salary

    @extend_schema(
        tags=["Salary"],
        responses={200: SALARY_DELETE_RESPONSE_SCHEMA},
    )
    def delete(self, request, *args, **kwargs):
        self.require_access(request.user)
        if not request.user.has_role("OWNER"):
            raise PermissionDenied(_("Sizga bu amalni bajarish mumkin emas."))
        salary = self.get_object()
        SalaryDeleteService.delete_salary(salary, deleted_by=request.user)
        return self.success({"message": _("Oylik o‘chirildi.")}, status=200)

