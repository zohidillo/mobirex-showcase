from src.bases.views import *

from .mixins import DebtAccessMixin


class PaidDebtsListView(DebtAccessMixin, BaseListView):
    model = models.Debt
    template_name = "debt/paid_list.html"
    paginate_by = 20

    def get_filtered_closed_debts_queryset(self, month_start=None):
        queryset = self.get_closed_debts_queryset(month_start=month_start)
        q = (self.request.GET.get("q") or "").strip()
        if q:
            queryset = queryset.filter(f_name__icontains=q)
        return queryset

    def get_queryset(self):
        month_start = self.get_selected_month_start(default_to_current=True)
        if month_start:
            return self.get_filtered_closed_debts_queryset(month_start=month_start)
        return self.get_filtered_closed_debts_queryset()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        year, month = self.get_selected_year_month(default_to_current=True)
        history_mode = self.get_payment_history_mode()
        context.update(
            {
                "year": str(year or ""),
                "month": str(month or ""),
                "q": self.request.GET.get("q", ""),
                "history_mode": history_mode,
                "year_options": self.get_year_options(
                    (self.get_closed_debts_queryset(), "added_at"),
                ),
                "month_choices": self.get_month_choices(),
                "history_mode_choices": self.get_payment_history_mode_choices(),
            }
        )
        return context
