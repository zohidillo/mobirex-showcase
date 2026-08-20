from src.bases.views import *


class PhoneCreateView(BaseCreateView):
    model = models.Phone
    form_class = forms.PhoneCreateForm
    template_name = "phone/create.html"
    success_url_name = "phone_unsold_list"

    def has_permission(self):
        return self.request.user.has_role("OWNER") or self.request.user.has_role("PHONE_SELLER")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def perform_create(self, form):
        user = self.request.user
        data = form.cleaned_data
        if user.has_role("OWNER"):
            data["branch"] = form.cleaned_data.get("branch")
        else:
            data["branch"] = user.get_primary_branch("PHONE_SELLER")
        return PhoneCreateService.create_phone(data, added_by=user)

    def form_valid(self, form):
        try:
            return super().form_valid(form)
        except Exception as exc:
            messages.error(self.request, str(exc))
            return super().form_invalid(form)
