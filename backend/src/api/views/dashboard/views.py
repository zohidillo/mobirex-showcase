from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _
from rest_framework.permissions import IsAuthenticated

from drf_spectacular.utils import OpenApiParameter, extend_schema

import src.core.models as models
from src.api.base import BaseAPIView
from src.services.dashboard import DashboardService
from src.shared.filters import get_default_year_month


class StaffDashboardAPIView(BaseAPIView):
    """
    Return phone or accessory seller dashboard data + comparison analytics.

    Params:
      branch_id  (int, required)
      role       (str, required)  PHONE_SELLER | ACCESSORY_SELLER
      staff_id   (int, optional)  owner can pass an employee id
      year       (int, optional)
      month      (int, optional)
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(
        parameters=[
            OpenApiParameter("branch_id", int, required=True),
            OpenApiParameter("role", str, required=True),
            OpenApiParameter("staff_id", int, required=False),
            OpenApiParameter("year", int, required=False),
            OpenApiParameter("month", int, required=False),
        ],
        responses={200: dict},
    )
    def get(self, request):
        user = request.user
        branch_id = request.query_params.get("branch_id")
        role = request.query_params.get("role", "").upper()
        staff_id = request.query_params.get("staff_id")

        if not branch_id:
            return self.error(_("branch_id majburiy."), status=400)
        if role not in ("PHONE_SELLER", "ACCESSORY_SELLER"):
            return self.error(_("role PHONE_SELLER yoki ACCESSORY_SELLER bo'lishi kerak."), status=400)

        try:
            branch_id = int(branch_id)
        except (TypeError, ValueError):
            return self.error(_("branch_id noto'g'ri."), status=400)

        branch = get_object_or_404(models.Branch, pk=branch_id)

        # Access control
        is_owner = user.has_role("OWNER") and models.BranchUser.objects.filter(
            branch=branch, user=user, role="OWNER", is_deleted=False
        ).exists()
        is_superuser = user.is_superuser

        if staff_id:
            # Owner/superuser viewing a specific staff member
            if not (is_owner or is_superuser):
                raise PermissionDenied(_("Ruxsat yo'q."))
            try:
                staff_id = int(staff_id)
            except (TypeError, ValueError):
                return self.error(_("staff_id noto'g'ri."), status=400)
            get_object_or_404(
                models.BranchUser,
                branch=branch,
                user_id=staff_id,
                role=role,
                is_deleted=False,
            )
        else:
            # Staff member viewing own dashboard
            is_own_role = models.BranchUser.objects.filter(
                branch=branch, user=user, role=role, is_deleted=False
            ).exists()
            if not (is_own_role or is_owner or is_superuser):
                raise PermissionDenied(_("Ruxsat yo'q."))

        year, month = get_default_year_month(request, source=request.path)

        if role == "PHONE_SELLER":
            role_scope = None
            data = DashboardService.get_phone_dashboard(branch, year, month)
            comparison = DashboardService.get_phone_dashboard_comparison(
                branch, year, month, current_data=data
            )
        else:
            role_scope = "ACCESSORY_ONLY" if not (is_owner or is_superuser) else "FULL"
            data = DashboardService.get_accessory_dashboard(branch, year, month, role_scope)
            comparison = DashboardService.get_accessory_dashboard_comparison(
                branch, year, month, role_scope=role_scope, current_data=data
            )

        from src.shared.json_utils import json_safe

        payload = json_safe(dict(data))
        payload["comparison"] = json_safe(comparison)
        return self.success(payload)
