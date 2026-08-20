from django.utils.translation import gettext_lazy as _

from src.bases.views import *
from src.shared.permissions import get_primary_seller_branch, user_matches_debt_domain


class DebtPaymentCreateView(BaseCreateView):
    model = models.DebtPayment
    form_class = forms.DebtPaymentForm
    template_name = "debt/payment_create.html"
    success_url_name = "debt_payment_list"

    def has_permission(self):
        return (
            self.request.user.has_role("OWNER")
            or self.request.user.has_role("PHONE_SELLER")
            or self.request.user.has_role("ACCESSORY_SELLER")
        )

    def _has_access(self, user, debt):
        if user.has_role("OWNER", debt.branch):
            return True
        primary = get_primary_seller_branch(user)
        return primary and primary.id == debt.branch_id and user_matches_debt_domain(user, debt)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        branch_id = self.request.GET.get("branch")
        if branch_id and self.request.user.has_role("OWNER"):
            try:
                branch_id_int = int(branch_id)
            except (TypeError, ValueError):
                branch_id_int = None
            if branch_id_int is not None:
                allowed_ids = [b.id for b in self.request.user.get_all_branches("OWNER") if b]
                if branch_id_int in allowed_ids:
                    branch = models.Branch.objects.filter(id=branch_id_int).first()
                    if branch:
                        kwargs["branch"] = branch
        return kwargs

    def perform_create(self, form):
        return DebtPaymentCreateService.create_payment(
            debt=form.cleaned_data.get("debt"),
            amount=form.cleaned_data.get("amount"),
            paid_by=self.request.user,
            note=form.cleaned_data.get("note"),
        )

    def form_valid(self, form):
        user = self.request.user
        debt = form.cleaned_data.get("debt")
        if not debt:
            return super().form_invalid(form)
        if user.has_role("OWNER"):
            selected_branch = form.cleaned_data.get("branch")
            if not selected_branch or debt.branch_id != selected_branch.id:
                messages.error(self.request, _("Sizga bu amalni bajarish mumkin emas."))
                return super().form_invalid(form)
        if not self._has_access(self.request.user, debt):
            messages.error(self.request, _("Sizga bu amalni bajarish mumkin emas."))
            return redirect("dashboard")
        try:
            return super().form_valid(form)
        except Exception as exc:
            messages.error(self.request, str(exc))
            return super().form_invalid(form)
