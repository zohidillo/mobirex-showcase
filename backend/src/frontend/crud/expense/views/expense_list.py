from django.db.models import Q
from django.utils.translation import gettext_lazy as _

from src.bases.views import *
from src.shared.filters import (
    MONTH_CHOICES,
    filter_by_month,
    get_available_years,
    get_default_year_month,
)
from src.shared.permissions import get_owner_branches, is_accessory_seller, is_owner, is_phone_seller


def _get_domain_seller_ids(branch, role):
    return set(
        models.BranchUser.objects.filter(
            branch=branch, role=role, is_deleted=False
        ).values_list("user_id", flat=True)
    )


class ExpenseListView(BaseListView):
    model = models.Expense
    template_name = "expense/expense_list.html"
    paginate_by = 20

    def has_permission(self):
        user = self.request.user
        return is_owner(user) or is_phone_seller(user) or is_accessory_seller(user)

    def _allowed_branches(self):
        user = self.request.user
        if user.is_superuser or user.is_cashier:
            return list(models.Branch.objects.filter(is_deleted=False))
        branches = []
        if user.has_role("OWNER"):
            branches.extend(user.get_all_branches("OWNER"))
        if user.has_role("PHONE_SELLER"):
            branches.extend(user.get_all_branches("PHONE_SELLER"))
        if user.has_role("ACCESSORY_SELLER"):
            branches.extend(user.get_all_branches("ACCESSORY_SELLER"))
        unique = {}
        for branch in branches:
            if branch:
                unique[branch.id] = branch
        return list(unique.values())

    def dispatch(self, request, *args, **kwargs):
        if not self.has_permission():
            messages.error(request, _("Sizga bu amalni bajarish mumkin emas."))
            return redirect("dashboard")
        return super().dispatch(request, *args, **kwargs)

    def get_base_queryset(self):
        user = self.request.user
        base_qs = models.Expense.objects.filter(is_deleted=False).select_related("branch", "created_by")

        if is_owner(user):
            owner_branches = get_owner_branches(user)
            owner_branch_ids = [branch.id for branch in owner_branches if branch]
            if not owner_branch_ids:
                return models.Expense.objects.none()
            queryset = base_qs.filter(branch_id__in=owner_branch_ids)

            branch_id = self.request.GET.get("branch")
            if branch_id:
                try:
                    branch_id_int = int(branch_id)
                except (TypeError, ValueError):
                    branch_id_int = None
                if branch_id_int in owner_branch_ids:
                    queryset = queryset.filter(branch_id=branch_id_int)

        elif is_phone_seller(user):
            branch = user.get_primary_branch("PHONE_SELLER")
            if not branch:
                return models.Expense.objects.none()
            seller_ids = _get_domain_seller_ids(branch, models.BranchUser.ROLE_PHONE_SELLER)
            queryset = base_qs.filter(
                Q(branch=branch, capital_type=models.Expense.CAPITAL_TYPE_PHONE)
                | Q(branch=branch, capital_type=None, created_by_id__in=seller_ids)
            )

        elif is_accessory_seller(user):
            branch = user.get_primary_branch("ACCESSORY_SELLER")
            if not branch:
                return models.Expense.objects.none()
            seller_ids = _get_domain_seller_ids(branch, models.BranchUser.ROLE_ACCESSORY_SELLER)
            queryset = base_qs.filter(
                Q(branch=branch, capital_type=models.Expense.CAPITAL_TYPE_ACCESSORY)
                | Q(branch=branch, capital_type=None, created_by_id__in=seller_ids)
            )

        else:
            return models.Expense.objects.none()

        expense_type = self.request.GET.get("type")
        creator_id = self.request.GET.get("created_by")

        if expense_type:
            queryset = queryset.filter(type=expense_type)

        if creator_id and is_owner(user):
            queryset = queryset.filter(created_by_id=creator_id)

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
        user = self.request.user
        year, month = get_default_year_month(
            self.request,
            source=self.request.path,
        )
        owner_branches = get_owner_branches(user) if is_owner(user) else []
        owner_branch_ids = [branch.id for branch in owner_branches if branch]
        selected_branch_id = self.request.GET.get("branch")
        employee_branch_ids = owner_branch_ids
        if selected_branch_id:
            try:
                selected_branch_id_int = int(selected_branch_id)
            except (TypeError, ValueError):
                selected_branch_id_int = None
            if selected_branch_id_int in owner_branch_ids:
                employee_branch_ids = [selected_branch_id_int]
        branch_employees = []
        if is_owner(user):
            seen = set()
            for bu in (
                models.BranchUser.objects.filter(branch_id__in=employee_branch_ids, is_deleted=False)
                .select_related("user")
                .order_by("user__username")
            ):
                if bu.user_id in seen:
                    continue
                seen.add(bu.user_id)
                branch_employees.append(bu.user)
        context.update(
            {
                "type": self.request.GET.get("type", ""),
                "created_by": self.request.GET.get("created_by", ""),
                "year": str(year or ""),
                "month": str(month or ""),
                "branch": self.request.GET.get("branch", ""),
                "owner_branches": owner_branches,
                "branch_employees": branch_employees,
                "can_manage_expenses": (
                    not is_owner(user)
                    and (is_phone_seller(user) or is_accessory_seller(user))
                ),
                "year_options": get_available_years(self.get_base_queryset(), "added_at"),
                "month_choices": MONTH_CHOICES,
            }
        )
        return context
