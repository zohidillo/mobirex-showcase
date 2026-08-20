from src.bases.views import *


class AccessoryDeleteView(BaseDeleteView):
    model = models.Accessory
    template_name = "accessory/delete_confirm.html"
    success_url_name = "accessory_unsold_list"

    def has_permission(self):
        return self.request.user.has_role("OWNER") or self.request.user.has_role("ACCESSORY_SELLER")

    def get_object(self):
        obj = get_object_or_404(
            models.Accessory.objects.filter(is_deleted=False).select_related("branch", "added_by"),
            pk=self.kwargs.get(self.pk_url_kwarg, None),
        )
        user = self.request.user
        if user.has_role("ACCESSORY_SELLER", obj.branch):
            if obj.added_by != user:
                raise PermissionDenied
        elif user.has_role("OWNER", obj.branch):
            pass
        else:
            raise PermissionDenied
        return obj

    def perform_delete(self, obj):
        AccessoryDeleteService.delete_accessory(obj, deleted_by=self.request.user)

    def post(self, request, *args, **kwargs):
        obj = self.get_object()
        try:
            return super().post(request, *args, **kwargs)
        except Exception as exc:
            messages.error(request, str(exc))
            return redirect(self.get_success_url())
