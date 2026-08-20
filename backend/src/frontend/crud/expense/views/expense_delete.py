from django.utils.translation import gettext_lazy as _

from src.bases.views import *
from src.shared.permissions import is_accessory_seller, is_owner, is_phone_seller, user_can_access_owner_branch


class ExpenseDeleteView(BaseDeleteView):
    model = models.Expense
    template_name = "expense/expense_delete.html"
    success_url_name = "expense_list"

    def has_permission(self):
        user = self.request.user
        return is_owner(user) or is_phone_seller(user) or is_accessory_seller(user)

    def _has_access(self, user, expense):
        if is_owner(user):
            return user_can_access_owner_branch(user, expense.branch)
        if expense.created_by_id != user.id:
            return False
        return user.has_role("PHONE_SELLER", expense.branch) or user.has_role(
            "ACCESSORY_SELLER", expense.branch
        )

    def dispatch(self, request, *args, **kwargs):
        if not self.has_permission():
            messages.error(request, _("Sizga bu amalni bajarish mumkin emas."))
            return redirect("dashboard")
        obj = get_object_or_404(
            models.Expense.objects.filter(is_deleted=False),
            pk=kwargs.get(self.pk_url_kwarg),
        )
        if not self._has_access(request.user, obj):
            messages.error(request, _("Sizga bu amalni bajarish mumkin emas."))
            return redirect("dashboard")
        self._object = obj
        return super().dispatch(request, *args, **kwargs)

    def get_object(self):
        if hasattr(self, "_object"):
            return self._object
        queryset = models.Expense.objects.filter(is_deleted=False)
        return get_object_or_404(queryset, pk=self.kwargs.get(self.pk_url_kwarg))

    def perform_delete(self, obj):
        ExpenseDeleteService.delete_expense(obj, deleted_by=self.request.user)

    def post(self, request, *args, **kwargs):
        try:
            return super().post(request, *args, **kwargs)
        except Exception as exc:
            messages.error(request, str(exc))
            return redirect(self.get_success_url())
