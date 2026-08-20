from django.utils.translation import gettext_lazy as _

from src.bases.views import *
from src.shared.permissions import is_accessory_seller, is_owner, is_phone_seller


class ExpenseCreateView(BaseCreateView):
    model = models.Expense
    form_class = forms.ExpenseForm
    template_name = "expense/expense_create.html"
    success_url_name = "expense_list"

    def has_permission(self):
        user = self.request.user
        return not is_owner(user) and (is_phone_seller(user) or is_accessory_seller(user))

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def perform_create(self, form):
        user = self.request.user
        data = dict(form.cleaned_data)
        branch = user.get_primary_branch("PHONE_SELLER") or user.get_primary_branch(
            "ACCESSORY_SELLER"
        )
        if not branch:
            raise ValueError(_("Filialga ruxsat yo‘q."))

        data["branch"] = branch
        data.pop("created_for", None)
        return ExpenseCreateService.create_expense(data, created_by=user)
