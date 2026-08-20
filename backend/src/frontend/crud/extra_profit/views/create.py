from django.utils.translation import gettext_lazy as _

from src.bases.views import *
from src.shared.permissions import is_phone_seller
from src.services.extra_profit.policy import get_seller_branch_and_capital_type


class ExtraProfitCreateView(BaseCreateView):
    model = models.ExtraProfit
    form_class = forms.ExtraProfitForm
    template_name = "extra_profit/create.html"
    success_url_name = "extra_profit_list"

    def has_permission(self):
        return is_phone_seller(self.request.user)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def perform_create(self, form):
        user = self.request.user
        data = form.cleaned_data
        branch, _ = get_seller_branch_and_capital_type(user)
        if not branch:
            raise PermissionDenied(_("Sizga bu amalni bajarish mumkin emas."))
        data["branch"] = branch
        return ExtraProfitCreateService.create_extra_profit(data, created_by=user)

    def form_valid(self, form):
        try:
            return super().form_valid(form)
        except Exception as exc:
            messages.error(self.request, str(exc))
            return super().form_invalid(form)
