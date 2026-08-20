from src.bases.views import *
from .mixins import DebtAccessMixin


class DebtListView(DebtAccessMixin, BaseListView):
    model = models.Debt
    template_name = "debt/debt_list.html"
    paginate_by = 20

    def get_filtered_queryset(self, queryset):
        user = self.request.user

        if user.has_role("OWNER"):
            branch_ids = [branch.id for branch in user.get_all_branches("OWNER") if branch]
            branch_id = self.request.GET.get("branch")
            if branch_id:
                try:
                    branch_id_int = int(branch_id)
                except (TypeError, ValueError):
                    branch_id_int = None
                if branch_id_int in branch_ids:
                    queryset = queryset.filter(branch_id=branch_id_int)

        creator_id = self.request.GET.get("created_by")
        if creator_id and user.has_role("OWNER"):
            queryset = queryset.filter(created_by_id=creator_id)

        debt_type = self.request.GET.get("type")
        q = (self.request.GET.get("q") or "").strip()

        if debt_type:
            queryset = queryset.filter(direction=debt_type)

        if q:
            queryset = queryset.filter(f_name__icontains=q)

        return queryset

    def get_queryset(self):
        selected_month_start = self.get_selected_month_start(default_to_current=True)
        self.is_read_only_month = bool(selected_month_start and not self.is_selected_month_current())
        queryset = self.get_accessible_debts(selected_month_start).filter(remaining_amount__gt=0)
        return self.get_filtered_queryset(queryset)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        branches, branch_users = self.get_owner_context()
        year, month = self.get_selected_year_month(default_to_current=True)
        history_mode = self.get_payment_history_mode()
        context.update(
            {
                "type": self.request.GET.get("type", ""),
                "branch": self.request.GET.get("branch", ""),
                "created_by": self.request.GET.get("created_by", ""),
                "year": str(year or ""),
                "month": str(month or ""),
                "q": self.request.GET.get("q", ""),
                "history_mode": history_mode,
                "branch_users": branch_users,
                "owner_branches": branches,
                "year_options": self.get_year_options(
                    (
                        self.get_filtered_queryset(
                            self.get_accessible_debts()
                        ),
                        "added_at",
                    ),
                ),
                "month_choices": self.get_month_choices(),
                "history_mode_choices": self.get_payment_history_mode_choices(),
                "is_read_only_month": bool(getattr(self, "is_read_only_month", False)),
            }
        )
        return context
