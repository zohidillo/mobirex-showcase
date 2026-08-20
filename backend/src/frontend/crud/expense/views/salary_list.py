from src.bases.views import *
from src.shared.filters import (
    MONTH_CHOICES,
    filter_by_month,
    get_available_years,
    get_default_year_month,
)
from src.shared.permissions import get_owner_branches


class SalaryListView(BaseListView):
    model = models.Salary
    template_name = "expense/salary_list.html"
    paginate_by = 20

    def has_permission(self):
        return self.request.user.has_role("OWNER")

    def get_base_queryset(self):
        user = self.request.user
        if not user.has_role("OWNER"):
            return models.Salary.objects.none()

        owner_branches = get_owner_branches(user)
        if not owner_branches:
            return models.Salary.objects.none()

        queryset = models.Salary.objects.filter(
            is_deleted=False,
            branch__in=owner_branches,
        ).select_related("employee", "branch", "created_by")

        employee_id = self.request.GET.get("employee")

        if employee_id:
            queryset = queryset.filter(employee_id=employee_id)

        return queryset

    def get_queryset(self):
        return filter_by_month(
            self.get_base_queryset(),
            self.request,
            field_name="added_at",
            default_to_current=True,
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        year, month = get_default_year_month(
            self.request,
            source=self.request.path,
        )
        context.update(
            {
                "employee": self.request.GET.get("employee", ""),
                "year": str(year or ""),
                "month": str(month or ""),
                "year_options": get_available_years(self.get_base_queryset(), "added_at"),
                "month_choices": MONTH_CHOICES,
            }
        )
        return context
