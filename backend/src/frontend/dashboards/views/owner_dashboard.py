from django.utils.translation import gettext_lazy as _

from src.bases.views.imports import *
from src.services.dashboard import DashboardService
from src.shared.permissions import get_owner_branch_ids
from .accessory_seller_dashboard import AccessorySellerDashboardView
from .phone_seller_dashboard import PhoneSellerDashboardView


class OwnerBranchListView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        if not request.user.has_role("OWNER"):
            messages.error(request, _("Sizga bu sahifaga kirish mumkin emas."))
            return redirect("dashboard")
        branches = DashboardService.get_owner_branches(request.user)
        return render(
            request,
            "dashboards/owner_branch_list.html",
            {"branches": branches},
        )


class OwnerBranchEmployeeListView(LoginRequiredMixin, View):
    def get(self, request, branch_id, *args, **kwargs):
        if not request.user.has_role("OWNER"):
            messages.error(request, _("Sizga bu sahifaga kirish mumkin emas."))
            return redirect("dashboard")
        branch = get_object_or_404(
            models.Branch.objects.filter(id__in=get_owner_branch_ids(request.user)),
            pk=branch_id,
        )
        employees = DashboardService.get_branch_employees(branch)
        return render(
            request,
            "dashboards/owner_employee_list.html",
            {"branch": branch, "employees": employees},
        )


class OwnerEmployeeDashboardView(LoginRequiredMixin, View):
    def get(self, request, branch_id, employee_id, *args, **kwargs):
        if not request.user.has_role("OWNER"):
            messages.error(request, _("Sizga bu sahifaga kirish mumkin emas."))
            return redirect("dashboard")

        branch = get_object_or_404(
            models.Branch,
            pk=branch_id,
            id__in=get_owner_branch_ids(request.user),
        )
        branch_user = get_object_or_404(
            models.BranchUser,
            branch=branch,
            user_id=employee_id,
            is_deleted=False,
        )
        employee = branch_user.user

        request._owner_original_user = request.user
        request.user = employee

        if branch_user.role == "PHONE_SELLER":
            return PhoneSellerDashboardView.as_view()(request)
        if branch_user.role == "ACCESSORY_SELLER":
            return AccessorySellerDashboardView.as_view()(request)

        messages.error(request, _("Rol noto‘g‘ri."))
        return redirect("dashboard")
