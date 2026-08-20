from django.contrib import messages
from django.shortcuts import redirect
from django.utils.translation import gettext_lazy as _


class AdminRequiredMixin:
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, _("Sizga bu sahifaga kirish mumkin emas."))
            return redirect("dashboard")
        if not request.user.is_superuser:
            messages.error(request, _("Sizga bu sahifaga kirish mumkin emas."))
            return redirect("dashboard")
        return super().dispatch(request, *args, **kwargs)
