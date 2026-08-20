from django.utils.translation import gettext_lazy as _

from src.bases.views.imports import *
from src.services.dashboard import DashboardService


class CashierDashboardView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        if not request.user.is_superuser and not request.user.is_cashier:
            messages.error(request, _("Sizga bu sahifaga kirish mumkin emas."))
            return redirect("dashboard")
        data = DashboardService.get_cashier_dashboard()
        return render(request, "dashboards/cashier_dashboard.html", {"data": data})
