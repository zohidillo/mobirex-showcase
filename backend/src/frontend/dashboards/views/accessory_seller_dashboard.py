import json
from decimal import Decimal

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

class AccessorySellerDashboardView(LoginRequiredMixin, View):
    def get_year_choices(self, branch, role_scope):
        year_choices = set()
        expense_qs = models.Expense.objects.filter(branch=branch, is_deleted=False)
        debt_qs = models.Debt.objects.filter(branch=branch, is_deleted=False)
        payment_qs = models.DebtPayment.objects.filter(
            debt__branch=branch,
            debt__is_deleted=False,
            is_deleted=False,
        )

        if role_scope == "ACCESSORY_ONLY":
            role_filter = Q(created_by__branch_roles__branch=branch) & Q(
                created_by__branch_roles__is_deleted=False
            ) & (
                Q(created_by__branch_roles__role="ACCESSORY_SELLER")
                | Q(created_by__branch_roles__role="OWNER")
            )
            payment_role_filter = Q(paid_by__branch_roles__branch=branch) & Q(
                paid_by__branch_roles__is_deleted=False
            ) & (
                Q(paid_by__branch_roles__role="ACCESSORY_SELLER")
                | Q(paid_by__branch_roles__role="OWNER")
            )
            expense_qs = expense_qs.filter(role_filter)
            debt_qs = debt_qs.filter(role_filter).filter(
                Q(domain=models.Debt.DOMAIN_ACCESSORY) | Q(domain__isnull=True)
            )
            payment_qs = payment_qs.filter(payment_role_filter).filter(
                Q(debt__domain=models.Debt.DOMAIN_ACCESSORY) | Q(debt__domain__isnull=True)
            )

        sources = (
            (models.AccessoryCapital.objects.filter(branch=branch, is_deleted=False), "month"),
            (models.AccessorySale.objects.filter(branch=branch), "sold_at"),
            (expense_qs, "added_at"),
            (debt_qs, "added_at"),
            (payment_qs, "added_at"),
        )
        for queryset, date_field in sources:
            year_choices.update(get_available_years(queryset, date_field))
        return sorted(year_choices, reverse=True)

    def get(self, request, branch_id=None, *args, **kwargs):
        user = request.user
        branch = None

        role_scope = None
        if branch_id and user.has_role("OWNER"):
            branch = get_object_or_404(models.Branch, pk=branch_id, owner=user)
            role_scope = "FULL"
        elif branch_id and user.is_superuser:
            branch = get_object_or_404(models.Branch, pk=branch_id)
            role_scope = "FULL"
        elif user.has_role("ACCESSORY_SELLER"):
            branch = user.get_primary_branch("ACCESSORY_SELLER")
            if not branch or not user.has_role("ACCESSORY_SELLER", branch):
                messages.error(request, _("Sizga bu sahifaga kirish mumkin emas."))
                return redirect("dashboard")
            role_scope = "ACCESSORY_ONLY"
        elif user.has_role("OWNER"):
            messages.error(request, _("Sizga bu sahifaga kirish mumkin emas."))
            return redirect("owner-branches")
        else:
            messages.error(request, _("Sizga bu sahifaga kirish mumkin emas."))
            return redirect("dashboard")

        year, month = get_default_year_month(request, source=request.path)

        start_date, end_date = DashboardService.resolve_period(year, month)
        data = DashboardService.get_accessory_dashboard(
            branch=branch,
            year=year,
            month=month,
            role_scope=role_scope,
            start_date=start_date,
            end_date=end_date,
        )

        comparison = DashboardService.get_accessory_dashboard_comparison(
            branch=branch, year=year, month=month, role_scope=role_scope, current_data=data
        )

        sales_series = data.get("sales_series") or []
        for item in sales_series:
            item["amount"] = _to_number(item.get("amount"))

        pie_data = [
            {"label": _("Do‘kon qarzi"), "value": _to_number(data.get("store_owes"))},
            {"label": _("Qarz"), "value": _to_number(data.get("others_owe"))},
            {"label": _("Xarajat"), "value": _to_number(data.get("total_expense"))},
            {"label": _("Foyda"), "value": _to_number(data.get("accessory_profit"))},
        ]

        context = {
            "branch": branch,
            "year": year,
            "month": month,
            "year_choices": self.get_year_choices(branch, role_scope),
            "month_choices": MONTH_CHOICES,
            "invested_amount": data.get("invested_amount") or 0,
            "current_balance": data.get("current_balance") or 0,
            "accessory_profit": data.get("accessory_profit") or 0,
            "total_expense": data.get("total_expense") or 0,
            "shop_expense": data.get("shop_expense") or 0,
            "employee_expense": data.get("employee_expense") or 0,
            "store_owes": data.get("store_owes") or 0,
            "others_owe": data.get("others_owe") or 0,
            "debt_paid": data.get("debt_paid") or 0,
            "debt_returned": data.get("debt_returned") or 0,
            "total_accessory_types": data.get("total_accessory_types") or 0,
            "total_stock": data.get("total_stock") or 0,
            "total_inventory_value": data.get("total_inventory_value") or 0,
            "total_sold_value": data.get("total_sold_value") or 0,
            "total_quantity_sold": data.get("total_quantity_sold") or 0,
            "remaining_stock_value": data.get("remaining_stock_value") or 0,
            "sales_series_json": json.dumps(json_safe(sales_series)),
            "pie_data_json": json.dumps(json_safe(pie_data)),
            "comparison": comparison,
        }
        return render(request, "dashboards/accessory_seller_dashboard.html", context)
