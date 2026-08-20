from django.core.exceptions import ValidationError

from src.bases.views import *
from src.services.phone import PhoneService


class PhoneDeleteView(BaseDeleteView):
    model = models.Phone
    template_name = "phone/delete.html"
    success_url_name = "phone_unsold_list"

    def has_permission(self):
        return self.request.user.has_role("OWNER") or self.request.user.has_role("PHONE_SELLER")

    def get_queryset(self):
        return models.Phone.objects.filter(is_deleted=False).select_related("branch", "added_by")

    def get_object(self):
        obj = super().get_object()
        user = self.request.user
        if obj.is_deleted:
            raise PermissionDenied
        if user.has_role("PHONE_SELLER", obj.branch):
            if obj.added_by != user:
                raise PermissionDenied
        elif user.has_role("OWNER", obj.branch):
            pass
        else:
            raise PermissionDenied
        return obj

    def perform_delete(self, obj):
        PhoneService.delete_phone(obj, deleted_by=self.request.user)

    def post(self, request, *args, **kwargs):
        obj = self.get_object()
        try:
            return super().post(request, *args, **kwargs)
        except ValidationError as exc:
            messages.error(request, "; ".join(getattr(exc, "messages", [])) or str(exc))
            return redirect(self.get_success_url())
        except Exception as exc:
            messages.error(request, str(exc))
            return redirect(self.get_success_url())
