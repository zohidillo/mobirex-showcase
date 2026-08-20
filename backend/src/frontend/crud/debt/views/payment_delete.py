from django.utils.translation import gettext_lazy as _

from src.bases.views import *
from src.services.debt import is_debt_in_current_month
from src.shared.permissions import get_owner_branches


class DebtPaymentDeleteView(BaseDeleteView):
    model = models.DebtPayment
    template_name = "debt/payment_delete.html"
    success_url_name = "debt_payment_list"

    def has_permission(self):
        return self.request.user.has_role("OWNER")

    def _has_access(self, user, payment):
        owner_branch_ids = {branch.id for branch in get_owner_branches(user)}
        return payment.debt.branch_id in owner_branch_ids

    def dispatch(self, request, *args, **kwargs):
        if not self.has_permission():
            messages.error(request, _("Sizga bu amalni bajarish mumkin emas."))
            return redirect("dashboard")
        obj = get_object_or_404(
            models.DebtPayment.objects.select_related("debt", "debt__branch", "debt__created_by"),
            pk=kwargs.get(self.pk_url_kwarg),
            is_deleted=False,
        )
        if not self._has_access(request.user, obj):
            messages.error(request, _("Sizga bu amalni bajarish mumkin emas."))
            return redirect("dashboard")
        if not is_debt_in_current_month(obj.debt):
            messages.error(request, _("To’lov faqat joriy oyda o’chirilishi mumkin."))
            return redirect(self.get_success_url())
        self._object = obj
        return super().dispatch(request, *args, **kwargs)

    def get_object(self):
        if hasattr(self, "_object"):
            return self._object
        obj = super().get_object()
        if obj.is_deleted:
            raise PermissionDenied
        if not self._has_access(self.request.user, obj):
            raise PermissionDenied
        return obj

    def perform_delete(self, obj):
        DebtPaymentDeleteService.delete_payment(obj, deleted_by=self.request.user)

    def post(self, request, *args, **kwargs):
        try:
            return super().post(request, *args, **kwargs)
        except Exception as exc:
            messages.error(request, str(exc))
            return redirect(self.get_success_url())
