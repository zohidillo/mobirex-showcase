from django.core.exceptions import PermissionDenied, ValidationError
from django.utils.translation import gettext_lazy as _

from src.bases.views import *
from src.services.accessory.returns import AccessoryReturnService

class AccessoryReturnView(LoginRequiredMixin, View):
    def get(self, request, pk, *args, **kwargs):
        sale = get_object_or_404(models.AccessorySale, pk=pk, is_deleted=False)
        user = request.user
        try:
            AccessoryReturnService.return_sale(sale, returned_by=user)
        except PermissionDenied as exc:
            messages.error(request, str(exc) or _("Sizga bu amalni bajarish mumkin emas."))
            return redirect("dashboard")
        except ValidationError as exc:
            messages.error(request, "; ".join(getattr(exc, "messages", [])) or str(exc))
            return redirect("accessory_sold_list")
        except Exception as exc:
            messages.error(request, str(exc))
            return redirect("accessory_sold_list")

        messages.success(request, _("Aksessuar qaytarilishi yakunlandi."))
        return redirect("accessory_sold_list")
