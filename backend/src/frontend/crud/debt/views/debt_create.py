from django.utils.translation import gettext_lazy as _

from src.bases.views import *
from src.shared.permissions import get_primary_seller_branch


class DebtCreateView(BaseCreateView):
    model = models.Debt
    form_class = forms.DebtCreateForm
    template_name = "debt/debt_create.html"
    success_url_name = "debt_list"

    def has_permission(self):
        return (
            self.request.user.has_role("PHONE_SELLER")
            or self.request.user.has_role("ACCESSORY_SELLER")
        )

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def perform_create(self, form):
        user = self.request.user
        branch = get_primary_seller_branch(user)
        return DebtCreateService.create_debt(
            branch=branch,
            f_name=form.cleaned_data.get("f_name"),
            amount=form.cleaned_data.get("amount"),
            direction=form.cleaned_data.get("direction"),
            created_by=user,
            note=form.cleaned_data.get("note"),
        )

    def form_valid(self, form):
        user = self.request.user
        branch = get_primary_seller_branch(user)
        if not branch:
            messages.error(self.request, _("Sizga bu amalni bajarish mumkin emas."))
            return redirect("dashboard")
        if not (user.has_role("PHONE_SELLER", branch) or user.has_role("ACCESSORY_SELLER", branch)):
            messages.error(self.request, _("Sizga bu amalni bajarish mumkin emas."))
            return redirect("dashboard")
        try:
            return super().form_valid(form)
        except Exception as exc:
            messages.error(self.request, str(exc))
            return super().form_invalid(form)
