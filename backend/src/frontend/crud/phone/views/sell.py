from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from src.bases.views import *
from src.services.phone import PhoneService


class PhoneSellView(LoginRequiredMixin, View):
    template_name = "phone/sell.html"

    def _has_access(self, user, branch):
        return user.has_role("PHONE_SELLER", branch) or user.has_role("OWNER", branch)

    def dispatch(self, request, *args, **kwargs):
        try:
            return super().dispatch(request, *args, **kwargs)
        except PermissionDenied:
            messages.error(request, _("Sizga bu sahifaga kirish mumkin emas."))
            return redirect("dashboard")

    def get_object(self):
        phone = get_object_or_404(models.Phone, pk=self.kwargs.get("pk"), is_deleted=False)
        if phone.is_sold:
            raise PermissionDenied
        return phone

    def get(self, request, *args, **kwargs):
        phone = self.get_object()
        if not self._has_access(request.user, phone.branch):
            messages.error(request, _("Sizga bu amalni bajarish mumkin emas."))
            return redirect("dashboard")
        form = forms.PhoneSellForm()
        return render(request, self.template_name, {"form": form, "phone": phone})

    def post(self, request, *args, **kwargs):
        phone = self.get_object()
        if not self._has_access(request.user, phone.branch):
            messages.error(request, _("Sizga bu amalni bajarish mumkin emas."))
            return redirect("dashboard")
        form = forms.PhoneSellForm(request.POST)
        if not form.is_valid():
            messages.error(request, _("Iltimos, xatolarni to‘g‘rilang."))
            return render(request, self.template_name, {"form": form, "phone": phone})
        try:
            PhoneService.sell_phone(
                phone,
                sell_price=form.cleaned_data["sell_price"],
                sold_by=request.user,
            )
            messages.success(request, _("Telefon muvaffaqiyatli sotildi."))
            return redirect(reverse("phone_sold_list"))
        except ValidationError as exc:
            messages.error(request, "; ".join(getattr(exc, "messages", [])) or str(exc))
            return render(request, self.template_name, {"form": form, "phone": phone})
        except Exception as exc:
            messages.error(request, str(exc))
            return render(request, self.template_name, {"form": form, "phone": phone})
