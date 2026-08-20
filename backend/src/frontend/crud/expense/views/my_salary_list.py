from src.bases.views import *
from src.shared.filters import filter_by_month, get_request_year_month


class MySalaryListView(BaseListView):
    model = models.Salary
    template_name = "expense/my_salary_list.html"
    paginate_by = 20

    def has_permission(self):
        return not self.request.user.has_role("OWNER")

    def get_queryset(self):
        queryset = models.Salary.objects.filter(
            is_deleted=False,
            employee=self.request.user,
        ).order_by("-added_at")

        return filter_by_month(
            queryset,
            self.request,
            field_name="added_at",
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        year, month = get_request_year_month(
            self.request,
            default_to_current=False,
            source=self.request.path,
        )
        context.update(
            {
                "year": str(year or ""),
                "month": str(month or ""),
            }
        )
        return context
