from django.utils.translation import gettext_lazy as _

from src.bases.views import *
from src.shared.permissions import user_can_access_owner_branch


class SalaryDeleteView(BaseDeleteView):
    model = models.Salary
    template_name = "expense/salary_delete_confirm.html"
    success_url_name = "salary_list"

    def has_permission(self):
        return self.request.user.has_role("OWNER")

    def get_object(self):
        queryset = models.Salary.objects.filter(is_deleted=False)
        obj = get_object_or_404(queryset, pk=self.kwargs.get(self.pk_url_kwarg))
        if not user_can_access_owner_branch(self.request.user, obj.branch):
            raise PermissionDenied
        return obj

    def perform_delete(self, obj):
        SalaryDeleteService.delete_salary(obj, deleted_by=self.request.user)

    def post(self, request, *args, **kwargs):
        obj = self.get_object()
        now = timezone.localtime()
        salary_added_at = timezone.localtime(obj.added_at)
        if salary_added_at.year != now.year or salary_added_at.month != now.month:
            messages.error(request, _("Oylik faqat joriy oyda o‘chirilishi mumkin."))
            return redirect(self.get_success_url())
        try:
            return super().post(request, *args, **kwargs)
        except Exception as exc:
            messages.error(request, str(exc))
            return redirect(self.get_success_url())
