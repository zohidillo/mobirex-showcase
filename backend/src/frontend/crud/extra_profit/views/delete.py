from django.utils.translation import gettext_lazy as _

from src.bases.views import *
from src.shared.permissions import is_owner, is_phone_seller
from src.services.extra_profit.policy import (
    can_delete_extra_profit,
    filter_extra_profit_queryset_for_user,
    is_current_month_extra_profit,
)


class ExtraProfitDeleteView(BaseDeleteView):
    model = models.ExtraProfit
    template_name = "extra_profit/delete.html"
    success_url_name = "extra_profit_list"

    def has_permission(self):
        user = self.request.user
        return is_owner(user) or is_phone_seller(user)

    def get_queryset(self):
        queryset = (
            models.ExtraProfit.objects.filter(is_deleted=False)
            .select_related("branch", "created_by")
            .order_by("-added_at")
        )
        return filter_extra_profit_queryset_for_user(queryset, self.request.user)

    def get_object(self):
        obj = super().get_object()
        if not can_delete_extra_profit(self.request.user, obj):
            if not is_current_month_extra_profit(obj):
                messages.error(self.request, _("Qo'shimcha foyda faqat joriy oyda o'chirilishi mumkin."))
            raise PermissionDenied
        return obj

    def perform_delete(self, obj):
        ExtraProfitDeleteService.delete_extra_profit(obj, deleted_by=self.request.user)

    def post(self, request, *args, **kwargs):
        obj = self.get_object()
        try:
            return super().post(request, *args, **kwargs)
        except Exception as exc:
            messages.error(request, str(exc))
            return redirect(self.get_success_url())
