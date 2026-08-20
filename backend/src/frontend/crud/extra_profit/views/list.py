from django.utils import timezone

from src.bases.views import *
from src.shared.filters import (
    MONTH_CHOICES,
    filter_by_month,
    get_available_years,
    get_default_year_month,
)
from src.shared.permissions import is_owner, is_phone_seller
from src.services.extra_profit.policy import (
    filter_extra_profit_queryset_for_user,
    get_owned_branches_for_extra_profit,
)


class ExtraProfitListView(BaseListView):
    model = models.ExtraProfit
    template_name = "extra_profit/list.html"
    paginate_by = 20

    def has_permission(self):
        user = self.request.user
        return is_owner(user) or is_phone_seller(user)

    def get_base_queryset(self):
        user = self.request.user
        queryset = (
            models.ExtraProfit.objects.filter(is_deleted=False)
            .select_related(
                "branch",
                "created_by",
            )
            .order_by("-added_at")
        )
        queryset = filter_extra_profit_queryset_for_user(queryset, user)

        if is_owner(user):
            branches = get_owned_branches_for_extra_profit(user)
            branch_ids = [b.id for b in branches if b]
            branch_id = self.request.GET.get("branch")
            if branch_id:
                try:
                    branch_id_int = int(branch_id)
                except (TypeError, ValueError):
                    branch_id_int = None
                if branch_id_int in branch_ids:
                    queryset = queryset.filter(branch_id=branch_id_int)

        return queryset.order_by("-added_at")

    def get_queryset(self):
        queryset = filter_by_month(
            self.get_base_queryset(),
            self.request,
            field_name="added_at",
            default_to_current=True,
        )
        return queryset.order_by("-added_at")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        year, month = get_default_year_month(
            self.request,
            source=self.request.path,
        )
        owner_branches = []
        if is_owner(user):
            owner_branches = get_owned_branches_for_extra_profit(user)
        context.update(
            {
                "year": str(year or ""),
                "month": str(month or ""),
                "branch": self.request.GET.get("branch", ""),
                "owner_branches": owner_branches,
                "year_options": get_available_years(self.get_base_queryset(), "added_at"),
                "month_choices": MONTH_CHOICES,
                "can_create_extra_profit": is_phone_seller(user),
                "can_delete_extra_profit": (
                    (is_owner(user) or is_phone_seller(user))
                    and bool(year and month)
                    and int(year) == timezone.localdate().year
                    and int(month) == timezone.localdate().month
                ),
            }
        )
        return context
