from django.core.exceptions import PermissionDenied, ValidationError
from django.utils.translation import gettext_lazy as _

from src.bases.views import *
from src.services.phone import PhoneService


class PhoneReturnView(LoginRequiredMixin, View):
    def get(self, request, pk, *args, **kwargs):
        phone = get_object_or_404(models.Phone, pk=pk, is_deleted=False, is_sold=True)
        user = request.user
        try:
            PhoneService.return_phone(phone, returned_by=user)
        except PermissionDenied as exc:
            messages.error(request, str(exc) or _("Sizga bu amalni bajarish mumkin emas."))
            return redirect("dashboard")
        except ValidationError as exc:
            messages.error(request, "; ".join(getattr(exc, "messages", [])) or str(exc))
            return redirect("phone_sold_list")
        except Exception as exc:
            messages.error(request, str(exc))
            return redirect("phone_sold_list")

        messages.success(request, _("Telefon qaytarilishi yakunlandi."))
        return redirect("phone_sold_list")
