from src.bases.views import *
from src.shared.permissions import get_owner_branches


class AccessoryCreateView(BaseCreateView):
    model = models.Accessory
    form_class = forms.AccessoryCreateForm
    template_name = "accessory/create.html"
    success_url_name = "accessory_unsold_list"

    def has_permission(self):
        return self.request.user.has_role("OWNER") or self.request.user.has_role("ACCESSORY_SELLER")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def perform_create(self, form):
        user = self.request.user
        data = dict(form.cleaned_data)
        if user.has_role("OWNER"):
            branch = form.cleaned_data.get("branch")
            allowed_ids = {branch.id for branch in get_owner_branches(user)}
            if not branch or branch.id not in allowed_ids:
                raise ValueError(_("Filial tanlash shart."))
            data["branch"] = branch
        else:
            branch = user.get_primary_branch("ACCESSORY_SELLER")
            if not branch:
                raise ValueError(_("Filialga ruxsat yo‘q."))
            data["branch"] = branch
        data["added_by"] = user
        return AccessoryCreateService.create_accessory(data, added_by=user)

    def form_valid(self, form):
        try:
            return super().form_valid(form)
        except Exception as exc:
            messages.error(self.request, str(exc))
            return super().form_invalid(form)
