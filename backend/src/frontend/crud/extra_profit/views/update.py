from django.utils.translation import gettext_lazy as _

from src.bases.views import *


class ExtraProfitUpdateView(BaseUpdateView):
    model = models.ExtraProfit
    form_class = forms.ExtraProfitForm
    template_name = "extra_profit/update.html"
    success_url_name = "extra_profit_list"

    def dispatch(self, request, *args, **kwargs):
        raise PermissionDenied

    def has_permission(self):
        return self.request.user.has_role("OWNER") or self.request.user.has_role("PHONE_SELLER")

    def dispatch(self, request, *args, **kwargs):
        if request.user.has_role("ACCESSORY_SELLER"):
            messages.error(request, _("Sizga bu sahifaga kirish mumkin emas."))
            return redirect("dashboard")
        return super().dispatch(request, *args, **kwargs)

    def get_object(self, queryset=None):
        obj = super().get_object(queryset=queryset)
        user = self.request.user
        if obj.is_deleted:
            raise PermissionDenied
        if user.has_role("PHONE_SELLER", obj.branch):
            if obj.created_by != user:
                raise PermissionDenied
        elif user.has_role("OWNER", obj.branch):
            pass
        else:
            raise PermissionDenied
        return obj

    def perform_update(self, form):
        extra_profit = self.get_object()
        return ExtraProfitUpdateService.update_extra_profit(
            extra_profit,
            validated_data=form.cleaned_data,
            updated_by=self.request.user,
        )

    def form_valid(self, form):
        try:
            return super().form_valid(form)
        except Exception as exc:
            messages.error(self.request, str(exc))
            return super().form_invalid(form)
