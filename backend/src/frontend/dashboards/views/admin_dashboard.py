from django.utils.translation import gettext_lazy as _

from src.bases.views.imports import *
from src.services.dashboard import DashboardService


class AdminDashboardView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            messages.error(request, _("Sizga bu sahifaga kirish mumkin emas."))
            return redirect("dashboard")
        data = DashboardService.get_admin_dashboard()
        return render(request, "dashboards/admin_dashboard.html", {"data": data})
