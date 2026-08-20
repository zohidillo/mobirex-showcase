from datetime import date

from django.db.models import Prefetch, Q
from django.utils.translation import gettext_lazy as _

from src.bases.views import *
from src.services.debt import (
    filter_debts_for_month,
    filter_payments_by_debt_month,
    get_closed_debts_queryset,
    get_month_window,
    is_current_month,
)
from src.shared.filters import (
    MONTH_CHOICES,
    get_available_years,
    get_default_year_month,
    get_month_bounds,
    get_request_year_month,
)
from src.shared.permissions import get_primary_seller_branch, get_seller_domain_for_branch

PAYMENT_HISTORY_MODE_CHOICES = (
    ("selected", _("Tanlangan oy bo‘yicha")),
    ("full", _("To‘liq tarix")),
)


class DebtAccessMixin:
    def has_permission(self):
        user = self.request.user
        return (
            user.has_role("OWNER")
            or user.has_role("PHONE_SELLER")
            or user.has_role("ACCESSORY_SELLER")
        )

    def dispatch(self, request, *args, **kwargs):
        if not self.has_permission():
            messages.error(request, _("Sizga bu amalni bajarish mumkin emas."))
            return redirect("dashboard")
        return super().dispatch(request, *args, **kwargs)

    def get_selected_year_month(self, *, default_to_current=False):
        if default_to_current:
            return get_default_year_month(
                self.request,
                source=self.request.path,
            )
        return get_request_year_month(
            self.request,
            default_to_current=default_to_current,
            source=self.request.path,
        )

    def get_selected_month_start(self, *, default_to_current=False):
        year, month = self.get_selected_year_month(default_to_current=default_to_current)
        if not year or not month:
            return None
        return date(year, month, 1)

    def is_selected_month_current(self):
        selected_month_start = self.get_selected_month_start(default_to_current=True)
        return is_current_month(selected_month_start)

    def get_payment_history_mode(self):
        mode = (self.request.GET.get("history_mode") or "selected").strip().lower()
        return "full" if mode == "full" else "selected"

    def get_payment_prefetch(self):
        selected_month_start = self.get_selected_month_start(default_to_current=True)
        payments_qs = (
            models.DebtPayment.objects.filter(is_deleted=False)
            .select_related("paid_by", "debt", "debt__created_by", "debt__branch")
            .order_by("added_at", "id")
        )
        if self.get_payment_history_mode() == "selected" and selected_month_start:
            _, _, _, next_month_start_dt = get_month_window(selected_month_start)
            payments_qs = payments_qs.filter(added_at__lt=next_month_start_dt)
        return Prefetch("payments", queryset=payments_qs, to_attr="prefetched_payments")

    def get_base_debt_queryset(self):
        return (
            models.Debt.objects.filter(is_deleted=False)
            .select_related("branch", "created_by")
            .prefetch_related(self.get_payment_prefetch())
        )

    def get_base_payment_queryset(self):
        return (
            models.DebtPayment.objects.filter(
                is_deleted=False,
                debt__is_deleted=False,
            )
            .select_related("debt", "debt__branch", "debt__created_by", "paid_by")
            .order_by("-added_at", "-id")
        )

    def get_accessible_debts(self, month_start=None, *, default_to_current=False):
        user = self.request.user
        queryset = self.get_base_debt_queryset()

        if user.has_role("OWNER"):
            branch_ids = [branch.id for branch in user.get_all_branches("OWNER") if branch]
            if not branch_ids:
                return models.Debt.objects.none()
            queryset = queryset.filter(branch_id__in=branch_ids)
        elif user.has_role("PHONE_SELLER") or user.has_role("ACCESSORY_SELLER"):
            branch = get_primary_seller_branch(user)
            if not branch:
                return models.Debt.objects.none()
            queryset = queryset.filter(branch=branch)
            seller_domain = get_seller_domain_for_branch(user, branch)
            if seller_domain == models.Debt.DOMAIN_ACCESSORY:
                queryset = queryset.filter(domain=models.Debt.DOMAIN_ACCESSORY)
            elif seller_domain == models.Debt.DOMAIN_PHONE:
                queryset = queryset.filter(Q(domain=models.Debt.DOMAIN_PHONE) | Q(domain__isnull=True))
            else:
                return models.Debt.objects.none()
        else:
            return models.Debt.objects.none()

        return filter_debts_for_month(
            queryset,
            month_start,
            default_to_current=default_to_current,
        )

    def get_accessible_payments(self, month_start=None, *, default_to_current=False):
        user = self.request.user
        queryset = self.get_base_payment_queryset()

        if user.has_role("OWNER"):
            branch_ids = [branch.id for branch in user.get_all_branches("OWNER") if branch]
            if not branch_ids:
                return models.DebtPayment.objects.none()
            queryset = queryset.filter(debt__branch_id__in=branch_ids)
        elif user.has_role("PHONE_SELLER") or user.has_role("ACCESSORY_SELLER"):
            branch = get_primary_seller_branch(user)
            if not branch:
                return models.DebtPayment.objects.none()
            queryset = queryset.filter(debt__branch=branch)
            seller_domain = get_seller_domain_for_branch(user, branch)
            if seller_domain == models.Debt.DOMAIN_ACCESSORY:
                queryset = queryset.filter(debt__domain=models.Debt.DOMAIN_ACCESSORY)
            elif seller_domain == models.Debt.DOMAIN_PHONE:
                queryset = queryset.filter(
                    Q(debt__domain=models.Debt.DOMAIN_PHONE) | Q(debt__domain__isnull=True)
                )
            else:
                return models.DebtPayment.objects.none()
        else:
            return models.DebtPayment.objects.none()

        return filter_payments_by_debt_month(
            queryset,
            month_start,
            default_to_current=default_to_current,
        )

    def get_month_date_range(self, year, month):
        return get_month_bounds(year, month, default_to_current=False, source=self.request.path)

    def get_closed_debts_queryset(self, month_start=None):
        queryset = self.get_accessible_debts()
        return get_closed_debts_queryset(queryset=queryset, month=month_start)

    def get_year_options(self, *sources):
        years = set()
        for queryset, date_field in sources:
            years.update(get_available_years(queryset, date_field))
        return sorted(years, reverse=True)

    def get_month_choices(self):
        return MONTH_CHOICES

    def get_payment_history_mode_choices(self):
        return PAYMENT_HISTORY_MODE_CHOICES

    def get_owner_context(self):
        user = self.request.user
        if not user.has_role("OWNER"):
            return [], []

        branches = user.get_all_branches("OWNER")
        seen = set()
        branch_users = []
        for branch_user in (
            models.BranchUser.objects.filter(branch__in=branches, is_deleted=False)
            .select_related("user")
            .order_by("user__username")
        ):
            if branch_user.user_id in seen:
                continue
            seen.add(branch_user.user_id)
            branch_users.append(branch_user.user)

        return branches, branch_users
