import json
from datetime import date
from decimal import Decimal

from django.core.cache import cache
from django.utils import timezone
from django.utils.translation import gettext as _

from src.bases.views.imports import *
from src.services.dashboard import DashboardService
from src.shared.filters import MONTH_CHOICES, get_available_years, get_default_year_month
from src.shared.json_utils import json_safe


def _to_number(value):
    if value is None:
        return 0
    if isinstance(value, Decimal):
        return float(value)
    return float(value)

class PhoneSellerDashboardView(LoginRequiredMixin, View):
    def get_year_choices(self, branch):
        year_choices = set()
        role_filter = Q(created_by__branch_roles__branch=branch) & Q(
            created_by__branch_roles__is_deleted=False
        ) & (
            Q(created_by__branch_roles__role="PHONE_SELLER")
            | Q(created_by__branch_roles__role="OWNER")
        )
        payment_role_filter = Q(paid_by__branch_roles__branch=branch) & Q(
            paid_by__branch_roles__is_deleted=False
        ) & (
            Q(paid_by__branch_roles__role="PHONE_SELLER")
            | Q(paid_by__branch_roles__role="OWNER")
        )
        sources = (
            (models.PhoneCapital.objects.filter(branch=branch, is_deleted=False), "month"),
            (models.Phone.objects.filter(branch=branch, is_deleted=False), "added_at"),
            (models.Phone.objects.filter(branch=branch, is_deleted=False, is_sold=True), "sold_at"),
            (
                models.Expense.objects.filter(branch=branch, is_deleted=False).filter(role_filter),
                "added_at",
            ),
            (
                models.ExtraProfit.objects.filter(branch=branch, is_deleted=False).filter(role_filter),
                "added_at",
            ),
            (
                models.Debt.objects.filter(
                    branch=branch,
                    is_deleted=False,
                )
                .filter(role_filter)
                .filter(Q(domain=models.Debt.DOMAIN_PHONE) | Q(domain__isnull=True)),
                "added_at",
            ),
            (
                models.DebtPayment.objects.filter(
                    debt__branch=branch,
                    debt__is_deleted=False,
                    is_deleted=False,
                )
                .filter(payment_role_filter)
                .filter(Q(debt__domain=models.Debt.DOMAIN_PHONE) | Q(debt__domain__isnull=True)),
                "added_at",
            ),
        )
        for queryset, date_field in sources:
            year_choices.update(get_available_years(queryset, date_field))
        return sorted(year_choices, reverse=True)

    def get(self, request, *args, **kwargs):
        user = request.user
        branch = user.get_primary_branch("PHONE_SELLER")
        if not branch or not user.has_role("PHONE_SELLER", branch):
            messages.error(request, _("Sizga bu sahifaga kirish mumkin emas."))
            return redirect("dashboard")

        year, month = get_default_year_month(request, source=request.path)

        start_date, end_date = DashboardService.resolve_period(year, month)
        current_month = timezone.localdate().replace(day=1)
        selected_month = date(year, month, 1)
        cache_key = f"dashboard:phone_seller:{branch.id}:{user.id}:{year}:{month}"
        if selected_month == current_month:
            cached_context = cache.get(cache_key)
            if cached_context is not None:
                return render(request, "dashboards/phone_seller_dashboard.html", cached_context)

        data = DashboardService.get_phone_dashboard(
            branch=branch,
            year=year,
            month=month,
            start_date=start_date,
            end_date=end_date,
        )

        comparison = DashboardService.get_phone_dashboard_comparison(
            branch=branch, year=year, month=month, current_data=data
        )

        invested_amount = data.get("invested_amount") or 0
        current_balance = data.get("current_balance") or 0
        phone_profit = data.get("phone_profit") or 0
        extra_profit = data.get("extra_profit") or 0
        net_profit = data.get("net_profit") or 0
        total_expense = data.get("total_expense") or 0
        shop_expense = data.get("shop_expense") or 0
        employee_expense = data.get("employee_expense") or 0
        store_owes = data.get("store_owes") or 0
        others_owe = data.get("others_owe") or 0
        debt_paid = data.get("debt_paid") or 0
        debt_returned = data.get("debt_returned") or 0
        phones_bought_count = data.get("phones_bought_count") or 0
        phones_sold_count = data.get("phones_sold_count") or 0
        phones_remaining_count = data.get("phones_remaining_count") or 0
        total_cost_bought = data.get("total_cost_bought") or 0
        total_sold_value = data.get("total_sold_value") or 0
        remaining_value = data.get("remaining_value") or 0
        sales_series = data.get("sales_series") or []
        for item in sales_series:
            item["amount"] = _to_number(item["amount"])

        pie_data = [
            # {"label": "Balans", "value": _to_number(current_balance)},
            {"label": _("Foyda"), "value": _to_number(net_profit)},
            {"label": _("Do‘kon qarzi"), "value": _to_number(store_owes)},
            {"label": _("Qarz"), "value": _to_number(others_owe)},
            {"label": _("Xarajat"), "value": _to_number(total_expense)},
        ]

        context = {
            "branch": branch,
            "year": year,
            "month": month,
            "year_choices": self.get_year_choices(branch),
            "month_choices": MONTH_CHOICES,
            "invested_amount": invested_amount,
            "current_balance": current_balance,
            "phone_profit": phone_profit,
            "extra_profit": extra_profit,
            "net_profit": net_profit,
            "total_expense": total_expense,
            "shop_expense": shop_expense,
            "employee_expense": employee_expense,
            "store_owes": store_owes,
            "others_owe": others_owe,
            "debt_paid": debt_paid,
            "debt_returned": debt_returned,
            "phones_bought_count": phones_bought_count,
            "phones_sold_count": phones_sold_count,
            "phones_remaining_count": phones_remaining_count,
            "total_cost_bought": total_cost_bought,
            "total_sold_value": total_sold_value,
            "remaining_value": remaining_value,
            "sales_series_json": json.dumps(json_safe(sales_series)),
            "pie_data_json": json.dumps(json_safe(pie_data)),
            "current_balance_value": _to_number(current_balance),
            "comparison": comparison,
        }
        if selected_month == current_month:
            cache.set(cache_key, context, 30)
        return render(request, "dashboards/phone_seller_dashboard.html", context)
