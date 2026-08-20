from django.utils.translation import gettext_lazy as _

from src.bases.views import *
from src.services.debt import is_debt_in_current_month
from src.shared.permissions import get_primary_seller_branch, user_matches_debt_domain


class DebtDeleteView(BaseDeleteView):
    model = models.Debt
    template_name = "debt/debt_delete.html"
    success_url_name = "debt_list"

    def has_permission(self):
        return (
            self.request.user.has_role("OWNER")
            or self.request.user.has_role("PHONE_SELLER")
            or self.request.user.has_role("ACCESSORY_SELLER")
        )

    def _has_access(self, user, debt):
        if user.has_role("OWNER", debt.branch):
            return True
        if debt.created_by_id != user.id:
            return False
        primary = get_primary_seller_branch(user)
        return primary and primary.id == debt.branch_id and user_matches_debt_domain(user, debt)

    def dispatch(self, request, *args, **kwargs):
        if not self.has_permission():
            messages.error(request, _("Sizga bu amalni bajarish mumkin emas."))
            return redirect("dashboard")
        obj = get_object_or_404(
            models.Debt.objects.filter(is_deleted=False),
            pk=kwargs.get(self.pk_url_kwarg),
        )
        if not self._has_access(request.user, obj):
            messages.error(request, _("Sizga bu amalni bajarish mumkin emas."))
            return redirect("dashboard")
        if not is_debt_in_current_month(obj):
            messages.error(request, _("Qarz faqat joriy oyda o‘chirilishi mumkin."))
            return redirect(self.get_success_url())
        self._object = obj
        return super().dispatch(request, *args, **kwargs)

    def get_object(self):
        if hasattr(self, "_object"):
            return self._object
        queryset = models.Debt.objects.filter(is_deleted=False)
        return get_object_or_404(queryset, pk=self.kwargs.get(self.pk_url_kwarg))

    def perform_delete(self, obj):
        DebtDeleteService.delete_debt(obj, deleted_by=self.request.user)

    def post(self, request, *args, **kwargs):
        try:
            return super().post(request, *args, **kwargs)
        except Exception as exc:
            messages.error(request, str(exc))
            return redirect(self.get_success_url())
