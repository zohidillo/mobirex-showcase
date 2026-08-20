from src.bases.views import *
from src.shared.permissions import get_owner_branch_ids


class SalaryCreateView(BaseCreateView):
    model = models.Salary
    form_class = forms.SalaryForm
    template_name = "expense/salary_create.html"
    success_url_name = "salary_list"

    def has_permission(self):
        return self.request.user.has_role("OWNER")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def perform_create(self, form):
        user = self.request.user
        employee = form.cleaned_data.get("employee")
        if not employee:
            raise PermissionDenied
        branch_user = (
            models.BranchUser.objects.filter(
                user=employee,
                branch_id__in=get_owner_branch_ids(user),
                is_deleted=False,
            )
            .select_related("branch")
            .order_by("-added_at")
            .first()
        )
        if not branch_user:
            raise PermissionDenied

        data = dict(form.cleaned_data)
        data["branch"] = branch_user.branch

        return SalaryCreateService.create_salary(data, created_by=user)

    def form_valid(self, form):
        try:
            return super().form_valid(form)
        except Exception as exc:
            messages.error(self.request, str(exc))
            return super().form_invalid(form)
