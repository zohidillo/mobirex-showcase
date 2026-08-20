from src.bases.views import *
from .mixins import DebtAccessMixin


class DebtPaymentListView(DebtAccessMixin, BaseListView):
    model = models.DebtPayment
    template_name = "debt/payment_list.html"
    paginate_by = 20

    def get_filtered_payments_queryset(self, month_start):
        queryset = self.get_accessible_payments(month_start, default_to_current=True)
        user = self.request.user
        if user.has_role("OWNER"):
            branch_id = self.request.GET.get("branch")
            if branch_id:
                try:
                    branch_id_int = int(branch_id)
                except (TypeError, ValueError):
                    branch_id_int = None
                branch_ids = [b.id for b in user.get_all_branches("OWNER") if b]
                if branch_id_int in branch_ids:
                    queryset = queryset.filter(debt__branch_id=branch_id_int)

        debt_id = self.request.GET.get("debt")
        if debt_id:
            queryset = queryset.filter(debt_id=debt_id)

        return queryset

    def get_month_debts_queryset(self, month_start):
        queryset = self.get_accessible_debts(
            month_start,
            default_to_current=True,
        ).select_related("branch", "created_by")
        user = self.request.user
        if user.has_role("OWNER"):
            branch_id = self.request.GET.get("branch")
            if branch_id:
                try:
                    branch_id_int = int(branch_id)
                except (TypeError, ValueError):
                    branch_id_int = None
                branch_ids = [branch.id for branch in user.get_all_branches("OWNER") if branch]
                if branch_id_int in branch_ids:
                    queryset = queryset.filter(branch_id=branch_id_int)
        return queryset.order_by("f_name", "id")

    def get_queryset(self):
        selected_month_start = self.get_selected_month_start(default_to_current=True)
        self.is_read_only_month = bool(selected_month_start and not self.is_selected_month_current())
        return self.get_filtered_payments_queryset(selected_month_start)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        branches, _ = self.get_owner_context()
        year, month = self.get_selected_year_month(default_to_current=True)
        selected_month_start = self.get_selected_month_start(default_to_current=True)
        context.update(
            {
                "debt": self.request.GET.get("debt", ""),
                "branch": self.request.GET.get("branch", ""),
                "year": str(year or ""),
                "month": str(month or ""),
                "debts": self.get_month_debts_queryset(selected_month_start),
                "owner_branches": branches,
                "year_options": self.get_year_options(
                    (self.get_accessible_debts(), "added_at"),
                ),
                "month_choices": self.get_month_choices(),
                "is_read_only_month": bool(getattr(self, "is_read_only_month", False)),
            }
        )
        return context
