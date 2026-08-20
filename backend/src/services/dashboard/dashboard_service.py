from collections import defaultdict, deque
from datetime import date, datetime, timedelta
from decimal import Decimal

from django.utils import timezone
from django.core.cache import cache
from django.db.models import Sum, Count, Q, F, DecimalField, ExpressionWrapper, Value
from django.db.models.functions import ExtractDay, TruncMonth, Coalesce

from src.core.models import (
    Branch,
    BranchUser,
    User as CustomUser,
    DashboardSnapshot,
    PhoneCapital,
    AccessoryCapital,
    Phone,
    Accessory,
    AccessorySale,
    Debt,
    DebtPayment,
    Expense,
    Salary,
    ExtraProfit,
    Payment,
)
from src.services.debt import filter_debts_for_month, filter_payments_by_debt_month
from src.shared.filters import get_current_year_month, normalize_year_month
from src.shared.json_utils import json_safe
from src.shared.permissions import get_owner_branches


def _make_aware(value):
    if timezone.is_naive(value):
        return timezone.make_aware(value)
    return value


def _resolve_period_with_override(year=None, month=None, start_date=None, end_date=None):
    if start_date is not None:
        start_date = _make_aware(start_date)
        if end_date is None:
            if start_date.month == 12:
                end_date = start_date.replace(year=start_date.year + 1, month=1)
            else:
                end_date = start_date.replace(month=start_date.month + 1)
        return start_date, end_date
    return DashboardService.resolve_period(year, month)


def _sum_or_zero(qs, field_name):
    return qs.aggregate(total=Sum(field_name))["total"] or 0


def _count_or_zero(qs, field_name="id"):
    return qs.aggregate(total=Count(field_name))["total"] or 0


def _months_back(year, month, count):
    base = year * 12 + (month - 1)
    months = []
    for offset in range(count - 1, -1, -1):
        value = base - offset
        y = value // 12
        m = value % 12 + 1
        months.append((y, m))
    return months


def _dashboard_cache_key(prefix, *parts):
    suffix = ":".join(str(part) for part in parts if part is not None)
    return f"dashboard:{prefix}:{suffix}"


def _month_start_from_datetime(value):
    return value.date().replace(day=1)


def _decimal_zero():
    return Value(
        Decimal("0.00"),
        output_field=DecimalField(max_digits=14, decimal_places=2),
    )


def _next_month_date(value):
    if value.month == 12:
        return date(value.year + 1, 1, 1)
    return date(value.year, value.month + 1, 1)


def _apply_role_scope_filter(qs, branch, role_scope, user_field="created_by"):
    scope = role_scope or "FULL"
    qs = qs.filter(
        Q(**{f"{user_field}__branch_roles__branch": branch}),
        Q(**{f"{user_field}__branch_roles__is_deleted": False}),
    )
    if scope == "PHONE_ONLY":
        qs = qs.filter(
            Q(**{f"{user_field}__branch_roles__role": "PHONE_SELLER"})
            | Q(**{f"{user_field}__branch_roles__role": "OWNER"})
        )
    elif scope == "ACCESSORY_ONLY":
        qs = qs.filter(
            Q(**{f"{user_field}__branch_roles__role": "ACCESSORY_SELLER"})
            | Q(**{f"{user_field}__branch_roles__role": "OWNER"})
        )
    return qs.distinct()


def _apply_debt_domain_scope_filter(qs, role_scope, *, field_name="domain"):
    scope = role_scope or "FULL"
    if scope == "PHONE_ONLY":
        return qs.filter(Q(**{field_name: "PHONE"}) | Q(**{f"{field_name}__isnull": True}))
    if scope == "ACCESSORY_ONLY":
        return qs.filter(Q(**{field_name: "ACCESSORY"}) | Q(**{f"{field_name}__isnull": True}))
    return qs


class DashboardService:
    @staticmethod
    def get_current_year_month(reference_time=None):
        _, year, month = get_current_year_month(reference_time)
        return year, month

    @staticmethod
    def normalize_period(year=None, month=None):
        return normalize_year_month(
            year,
            month,
            default_to_current=True,
            source="dashboard_service",
        )

    @staticmethod
    def resolve_period(year=None, month=None):
        year, month = DashboardService.normalize_period(year, month)
        start_date = _make_aware(datetime(year, month, 1))

        if start_date.month == 12:
            end_date = start_date.replace(year=start_date.year + 1, month=1)
        else:
            end_date = start_date.replace(month=start_date.month + 1)

        return start_date, end_date

    @staticmethod
    def _resolve_month_period(year=None, month=None, start_date=None, end_date=None):
        start_date, end_date = _resolve_period_with_override(year, month, start_date, end_date)
        return start_date, end_date, _month_start_from_datetime(start_date)

    @staticmethod
    def _is_current_month(month_start, *, reference_time=None):
        current_month = timezone.localdate(reference_time) if reference_time else timezone.localdate()
        return month_start == current_month.replace(day=1)

    @staticmethod
    def _get_dashboard_snapshot(branch, month_start):
        return DashboardSnapshot.objects.filter(branch=branch, month=month_start).first()

    @staticmethod
    def _with_snapshot_metadata(data, *, snapshot=None, month_start=None):
        result = dict(data or {})
        if snapshot is not None:
            result["from_snapshot"] = True
            result["snapshot_month"] = snapshot.month.isoformat()
            result["snapshot_created_at"] = snapshot.created_at.isoformat()
            return result

        if month_start is not None:
            result["from_snapshot"] = False
            result["snapshot_missing"] = True
            result["snapshot_month"] = month_start.isoformat()
        return result

    @staticmethod
    def _get_accessory_snapshot_data(snapshot, role_scope):
        data = snapshot.accessory_data or {}
        if "FULL" in data or "ACCESSORY_ONLY" in data:
            return data.get(role_scope or "FULL") or data.get("FULL") or {}
        return data

    @staticmethod
    def _old_close_month_phone_match_key(phone):
        return (
            phone.branch_id,
            phone.category_id,
            phone.name,
            phone.imei,
            phone.storage,
            phone.color,
            phone.from_by,
            phone.cost_price,
        )

    @staticmethod
    def get_old_close_month_phone_repair_matches(branch, month):
        month_start = month.replace(day=1)
        _, end_date = DashboardService.resolve_period(month_start.year, month_start.month)
        repair_end_date = _make_aware(datetime.combine(_next_month_date(end_date.date()), datetime.min.time()))
        last_day_start = end_date - timedelta(days=1)

        recreated_phones = list(
            Phone.all_objects.filter(
                branch=branch,
                for_month_close=True,
                added_at__gte=end_date,
                added_at__lt=repair_end_date,
            )
            .select_related("category", "branch")
            .order_by("added_at", "id")
        )
        original_phones = list(
            Phone.all_objects.filter(
                branch=branch,
                is_sold=True,
                sold_at__gte=last_day_start,
                sold_at__lt=end_date,
                sell_price=F("cost_price"),
            )
            .select_related("category", "branch")
            .order_by("sold_at", "id")
        )

        original_buckets = defaultdict(deque)
        for original_phone in original_phones:
            original_buckets[DashboardService._old_close_month_phone_match_key(original_phone)].append(
                original_phone
            )

        matches = []
        for recreated_phone in recreated_phones:
            bucket = original_buckets.get(
                DashboardService._old_close_month_phone_match_key(recreated_phone)
            )
            if not bucket:
                continue
            matches.append(
                {
                    "original_phone": bucket.popleft(),
                    "recreated_phone": recreated_phone,
                }
            )
        return matches

    @staticmethod
    def _is_phone_in_live_sales_window(phone, *, start_date, end_date):
        return bool(
            phone
            and not phone.is_deleted
            and phone.is_sold
            and phone.sold_at
            and start_date <= phone.sold_at < end_date
        )

    @staticmethod
    def _is_phone_in_live_remaining_inventory(phone):
        return bool(phone and not phone.is_deleted and not phone.is_sold)

    @staticmethod
    def _apply_old_close_month_phone_repair(payload, month, repair_matches):
        month_start = month.replace(day=1)
        start_date, end_date = DashboardService.resolve_period(month_start.year, month_start.month)

        phone_data = payload.get("phone_data") or {}
        dashboard_data = payload.get("dashboard_data") or {}
        profit_summary = dashboard_data.get("profit_summary") or {}
        inventory_summary = dashboard_data.get("inventory_summary") or {}

        excluded_sale_ids = set()
        excluded_sales_by_day = defaultdict(float)
        summary = {
            "recreated_phones_detected": len(repair_matches),
            "artificial_sales_excluded": 0,
            "inventory_phones_restored": 0,
        }

        for match in repair_matches:
            original_phone = match["original_phone"]
            recreated_phone = match["recreated_phone"]

            sale_value = float(original_phone.sell_price or 0)
            cost_value = float(recreated_phone.cost_price or 0)
            profit_value = float((original_phone.sell_price or 0) - (original_phone.cost_price or 0))

            if DashboardService._is_phone_in_live_sales_window(
                original_phone,
                start_date=start_date,
                end_date=end_date,
            ):
                summary["artificial_sales_excluded"] += 1
                phone_data["phones_sold_count"] = (phone_data.get("phones_sold_count") or 0) - 1
                phone_data["total_sold_value"] = (phone_data.get("total_sold_value") or 0) - sale_value
                phone_data["phone_profit"] = (phone_data.get("phone_profit") or 0) - profit_value
                phone_data["net_profit"] = (phone_data.get("net_profit") or 0) - profit_value

                profit_summary["phone_profit"] = (profit_summary.get("phone_profit") or 0) - profit_value
                profit_summary["net_profit"] = (profit_summary.get("net_profit") or 0) - profit_value
                inventory_summary["phones_sold_count"] = (
                    inventory_summary.get("phones_sold_count") or 0
                ) - 1

                excluded_sale_ids.add(original_phone.pk)
                if original_phone.sold_at:
                    excluded_sales_by_day[original_phone.sold_at.day] += sale_value

            if not DashboardService._is_phone_in_live_remaining_inventory(recreated_phone):
                summary["inventory_phones_restored"] += 1
                phone_data["phones_remaining_count"] = (
                    phone_data.get("phones_remaining_count") or 0
                ) + 1
                phone_data["remaining_value"] = (phone_data.get("remaining_value") or 0) + cost_value
                inventory_summary["phones_available_count"] = (
                    inventory_summary.get("phones_available_count") or 0
                ) + 1

        if excluded_sale_ids:
            dashboard_data["last_transactions"] = [
                item
                for item in (dashboard_data.get("last_transactions") or [])
                if not (
                    item.get("type") == "PHONE_SALE"
                    and item.get("object_id") in excluded_sale_ids
                )
            ]

        if excluded_sales_by_day:
            adjusted_sales_series = []
            for item in phone_data.get("sales_series") or []:
                amount_delta = excluded_sales_by_day.get(item.get("day"), 0)
                if not amount_delta:
                    adjusted_sales_series.append(item)
                    continue

                adjusted_amount = (item.get("amount") or 0) - amount_delta
                if adjusted_amount > 0:
                    updated_item = dict(item)
                    updated_item["amount"] = adjusted_amount
                    adjusted_sales_series.append(updated_item)
            phone_data["sales_series"] = adjusted_sales_series

        payload["phone_data"] = phone_data
        dashboard_data["profit_summary"] = profit_summary
        dashboard_data["inventory_summary"] = inventory_summary
        payload["dashboard_data"] = dashboard_data
        return summary

    @staticmethod
    def get_phone_capital_summary(
        branch=None,
        year=None,
        month=None,
        user=None,
        start_date=None,
        end_date=None,
    ):
        start_date, _ = _resolve_period_with_override(year, month, start_date, end_date)
        month_start = start_date.date()
        capital = None
        if user is not None:
            branches = user.get_all_branches()
            if not branches:
                return {"invested_amount": 0, "current_balance": 0}
            capital = (
                PhoneCapital.objects.filter(
                    branch__in=branches,
                    month=month_start,
                    is_deleted=False,
                )
                .select_related("branch")
                .order_by("-added_at")
                .first()
            )
        elif branch is not None:
            capital = PhoneCapital.objects.filter(
                branch=branch,
                month=month_start,
                is_deleted=False,
            ).first()
        if not capital:
            return {"invested_amount": 0, "current_balance": 0}
        return {
            "invested_amount": capital.invested_amount,
            "current_balance": capital.current_balance,
        }

    @staticmethod
    def get_accessory_capital_summary(
        branch=None,
        year=None,
        month=None,
        user=None,
        start_date=None,
        end_date=None,
    ):
        start_date, _ = _resolve_period_with_override(year, month, start_date, end_date)
        month_start = start_date.date()
        capital = None
        if user is not None:
            branches = user.get_all_branches()
            if not branches:
                return {"invested_amount": 0, "current_balance": 0}
            capital = (
                AccessoryCapital.objects.filter(
                    branch__in=branches,
                    month=month_start,
                    is_deleted=False,
                )
                .select_related("branch")
                .order_by("-added_at")
                .first()
            )
        elif branch is not None:
            capital = AccessoryCapital.objects.filter(
                branch=branch,
                month=month_start,
                is_deleted=False,
            ).first()
        if not capital:
            return {"invested_amount": 0, "current_balance": 0}
        return {
            "invested_amount": capital.invested_amount,
            "current_balance": capital.current_balance,
        }

    @staticmethod
    def get_debt_summary(
        branch,
        year=None,
        month=None,
        role_scope=None,
        start_date=None,
        end_date=None,
        debts_qs=None,
    ):
        start_date, end_date = _resolve_period_with_override(year, month, start_date, end_date)
        if debts_qs is None:
            debts_qs = Debt.objects.filter(
                branch=branch,
                is_deleted=False,
                remaining_amount__gt=0,
            ).select_related(
                "created_by",
                "branch",
            )
        else:
            debts_qs = debts_qs.filter(remaining_amount__gt=0)
        debts_qs = filter_debts_for_month(debts_qs, start_date)
        debts_qs = _apply_role_scope_filter(debts_qs, branch, role_scope, user_field="created_by")
        debts_qs = _apply_debt_domain_scope_filter(debts_qs, role_scope, field_name="domain")
        totals = debts_qs.aggregate(
            total_we_gave=Coalesce(
                Sum("amount", filter=Q(direction="WE_GAVE")),
                _decimal_zero(),
            ),
            total_we_took=Coalesce(
                Sum("amount", filter=Q(direction="WE_TOOK")),
                _decimal_zero(),
            ),
            remaining_we_gave=Coalesce(
                Sum("remaining_amount", filter=Q(direction="WE_GAVE")),
                _decimal_zero(),
            ),
            remaining_we_took=Coalesce(
                Sum("remaining_amount", filter=Q(direction="WE_TOOK")),
                _decimal_zero(),
            ),
        )
        return {
            "total_we_gave": totals.get("total_we_gave"),
            "total_we_took": totals.get("total_we_took"),
            "remaining_we_gave": totals.get("remaining_we_gave"),
            "remaining_we_took": totals.get("remaining_we_took"),
        }

    @staticmethod
    def get_expense_summary(
        branch,
        year=None,
        month=None,
        role_scope=None,
        start_date=None,
        end_date=None,
        expenses_qs=None,
    ):
        start_date, end_date = _resolve_period_with_override(year, month, start_date, end_date)
        if expenses_qs is None:
            expenses_qs = Expense.objects.filter(branch=branch, is_deleted=False).select_related(
                "created_by",
                "branch",
            )
        if start_date and end_date:
            expenses_qs = expenses_qs.filter(added_at__gte=start_date, added_at__lt=end_date)
        expenses_qs = _apply_role_scope_filter(expenses_qs, branch, role_scope, user_field="created_by")
        totals = expenses_qs.aggregate(
            total_expense=Sum("amount"),
            shop_expense_total=Sum("amount", filter=Q(type="SHOP_EXPENSE")),
            employee_expense_total=Sum("amount", filter=Q(type="EMPLOYEE_EXPENSE")),
        )
        return {
            "total_expense": totals.get("total_expense") or 0,
            "shop_expense_total": totals.get("shop_expense_total") or 0,
            "employee_expense_total": totals.get("employee_expense_total") or 0,
        }

    @staticmethod
    def get_salary_summary(
        branch,
        year=None,
        month=None,
        role_scope=None,
        start_date=None,
        end_date=None,
        salary_qs=None,
    ):
        start_date, end_date = _resolve_period_with_override(year, month, start_date, end_date)
        if salary_qs is None:
            salary_qs = Salary.objects.filter(branch=branch, is_deleted=False).select_related(
                "created_by",
                "branch",
            )
        if start_date and end_date:
            salary_qs = salary_qs.filter(added_at__gte=start_date, added_at__lt=end_date)
        salary_qs = _apply_role_scope_filter(salary_qs, branch, role_scope, user_field="created_by")
        total = salary_qs.aggregate(total=Sum("amount"))["total"] or 0
        return {"salary_total": total}

    @staticmethod
    def get_extra_profit_summary(
        branch,
        year=None,
        month=None,
        role_scope=None,
        start_date=None,
        end_date=None,
        extra_profit_qs=None,
    ):
        start_date, end_date = _resolve_period_with_override(year, month, start_date, end_date)
        if extra_profit_qs is None:
            extra_profit_qs = ExtraProfit.objects.filter(branch=branch, is_deleted=False)
        if start_date and end_date:
            extra_profit_qs = extra_profit_qs.filter(added_at__gte=start_date, added_at__lt=end_date)
        extra_profit_qs = _apply_role_scope_filter(
            extra_profit_qs,
            branch,
            role_scope,
            user_field="created_by",
        )
        total = extra_profit_qs.aggregate(total=Sum("amount"))["total"] or 0
        return {"extra_profit": total}

    @staticmethod
    def get_debt_payment_summary(
        branch,
        year=None,
        month=None,
        role_scope=None,
        start_date=None,
        end_date=None,
        payments_qs=None,
    ):
        start_date, end_date = _resolve_period_with_override(year, month, start_date, end_date)
        if payments_qs is None:
            payments_qs = DebtPayment.objects.filter(
                debt__branch=branch,
                debt__is_deleted=False,
                is_deleted=False,
            )
        payments_qs = filter_payments_by_debt_month(payments_qs, start_date)
        if start_date and end_date:
            payments_qs = payments_qs.filter(added_at__gte=start_date, added_at__lt=end_date)
        payments_qs = _apply_role_scope_filter(
            payments_qs,
            branch,
            role_scope,
            user_field="paid_by",
        )
        payments_qs = _apply_debt_domain_scope_filter(
            payments_qs,
            role_scope,
            field_name="debt__domain",
        )
        totals = payments_qs.aggregate(
            debt_paid=Sum("amount", filter=Q(debt__direction="WE_TOOK")),
            debt_returned=Sum("amount", filter=Q(debt__direction="WE_GAVE")),
        )
        return {
            "debt_paid": totals.get("debt_paid") or 0,
            "debt_returned": totals.get("debt_returned") or 0,
        }

    @staticmethod
    def get_profit_summary(
        branch,
        year=None,
        month=None,
        seller_id=None,
        role_scope="FULL",
        start_date=None,
        end_date=None,
        phones_qs=None,
        accessory_sales_qs=None,
        extra_profit_qs=None,
    ):
        start_date, end_date = _resolve_period_with_override(year, month, start_date, end_date)

        phone_profit = 0
        if role_scope in {"FULL", "PHONE_ONLY"}:
            if phones_qs is None:
                phones_qs = Phone.objects.filter(branch=branch, is_deleted=False).select_related(
                    "branch",
                    "sold_by",
                )
            phone_qs = phones_qs.filter(
                is_sold=True,
                sold_at__gte=start_date,
                sold_at__lt=end_date,
            )
            if seller_id:
                phone_qs = phone_qs.filter(sold_by_id=seller_id)
            totals = phone_qs.aggregate(total_sell=Sum("sell_price"), total_cost=Sum("cost_price"))
            phone_profit = (totals["total_sell"] or 0) - (totals["total_cost"] or 0)

        accessory_profit = 0
        if role_scope in {"FULL", "ACCESSORY_ONLY"}:
            if accessory_sales_qs is None:
                accessory_sales_qs = AccessorySale.objects.filter(branch=branch).select_related(
                    "branch",
                    "sold_by",
                    "accessory",
                )
            accessory_qs = accessory_sales_qs.filter(
                sold_at__gte=start_date,
                sold_at__lt=end_date,
            )
            if seller_id:
                accessory_qs = accessory_qs.filter(sold_by_id=seller_id)
            accessory_profit = accessory_qs.aggregate(total=Sum("profit"))["total"] or 0

        extra_profit = 0
        if role_scope == "FULL":
            if extra_profit_qs is None:
                extra_profit_qs = ExtraProfit.objects.filter(branch=branch, is_deleted=False)
            extra_qs = extra_profit_qs.filter(
                added_at__gte=start_date,
                added_at__lt=end_date,
            )
            extra_qs = _apply_role_scope_filter(extra_qs, branch, role_scope, user_field="created_by")
            extra_profit = extra_qs.aggregate(total=Sum("amount"))["total"] or 0

        net_profit = phone_profit + accessory_profit + extra_profit

        return {
            "phone_profit": phone_profit,
            "accessory_profit": accessory_profit,
            "extra_profit": extra_profit,
            "net_profit": net_profit,
        }

    @staticmethod
    def get_inventory_summary(
        branch,
        year=None,
        month=None,
        seller_id=None,
        role_scope="FULL",
        start_date=None,
        end_date=None,
        phones_qs=None,
        accessory_sales_qs=None,
    ):
        start_date, end_date = _resolve_period_with_override(year, month, start_date, end_date)

        phones_sold_count = 0
        phones_available_count = 0
        if role_scope in {"FULL", "PHONE_ONLY"}:
            if phones_qs is None:
                phones_qs = Phone.objects.filter(branch=branch, is_deleted=False).select_related(
                    "branch",
                    "sold_by",
                )
            sold_filter = Q(is_sold=True, sold_at__gte=start_date, sold_at__lt=end_date)
            if seller_id:
                sold_filter &= Q(sold_by_id=seller_id)
            phone_totals = phones_qs.aggregate(
                phones_sold_count=Count("id", filter=sold_filter),
                phones_available_count=Count("id", filter=Q(is_sold=False, is_month_closed=False)),
            )
            phones_sold_count = phone_totals.get("phones_sold_count") or 0
            phones_available_count = phone_totals.get("phones_available_count") or 0

        accessories_sold_count = 0
        accessories_in_stock_count = 0
        accessories_out_of_stock_count = 0
        if role_scope in {"FULL", "ACCESSORY_ONLY"}:
            if accessory_sales_qs is None:
                accessory_sales_qs = AccessorySale.objects.filter(branch=branch).select_related(
                    "branch",
                    "sold_by",
                    "accessory",
                )
            sale_qs = accessory_sales_qs.filter(
                sold_at__gte=start_date,
                sold_at__lt=end_date,
            )
            if seller_id:
                sale_qs = sale_qs.filter(sold_by_id=seller_id)
            accessories_sold_count = sale_qs.aggregate(total=Sum("quantity"))["total"] or 0

            accessory_qs = Accessory.objects.filter(branch=branch, is_deleted=False)
            stock_totals = accessory_qs.aggregate(
                accessories_in_stock_count=Sum("stock", filter=Q(stock__gt=0)),
                accessories_out_of_stock_count=Count("id", filter=Q(stock=0)),
            )
            accessories_in_stock_count = stock_totals.get("accessories_in_stock_count") or 0
            accessories_out_of_stock_count = stock_totals.get("accessories_out_of_stock_count") or 0

        return {
            "phones_sold_count": phones_sold_count,
            "phones_available_count": phones_available_count,
            "accessories_sold_count": accessories_sold_count,
            "accessories_in_stock_count": accessories_in_stock_count,
            "accessories_out_of_stock_count": accessories_out_of_stock_count,
        }

    @staticmethod
    def get_last_transactions(
        branch,
        year=None,
        month=None,
        seller_id=None,
        role_scope="FULL",
        start_date=None,
        end_date=None,
        phones_qs=None,
        accessory_sales_qs=None,
        expenses_qs=None,
        salary_qs=None,
        extra_profit_qs=None,
        payments_qs=None,
    ):
        start_date, end_date = _resolve_period_with_override(year, month, start_date, end_date)
        items = []

        if role_scope in {"FULL", "PHONE_ONLY"}:
            if phones_qs is None:
                phones_qs = Phone.objects.filter(branch=branch, is_deleted=False).select_related(
                    "branch",
                    "sold_by",
                )
            phone_qs = phones_qs.filter(
                is_sold=True,
                sold_at__gte=start_date,
                sold_at__lt=end_date,
            )
            if seller_id:
                phone_qs = phone_qs.filter(sold_by_id=seller_id)
            phone_rows = phone_qs.values("id", "sell_price", "cost_price", "sold_at").order_by(
                "-sold_at"
            )[:20]
            for row in phone_rows:
                sell_price = row["sell_price"] or 0
                cost_price = row["cost_price"] or 0
                items.append(
                    {
                        "type": "PHONE_SALE",
                        "object_id": row["id"],
                        "amount": sell_price,
                        "profit": sell_price - cost_price,
                        "occurred_at": row["sold_at"],
                    }
                )

        if role_scope in {"FULL", "ACCESSORY_ONLY"}:
            if accessory_sales_qs is None:
                accessory_sales_qs = AccessorySale.objects.filter(branch=branch).select_related(
                    "branch",
                    "sold_by",
                    "accessory",
                )
            accessory_qs = accessory_sales_qs.filter(
                sold_at__gte=start_date,
                sold_at__lt=end_date,
            )
            if seller_id:
                accessory_qs = accessory_qs.filter(sold_by_id=seller_id)
            accessory_rows = accessory_qs.values(
                "id", "total_price", "profit", "sold_at"
            ).order_by("-sold_at")[:20]
            for row in accessory_rows:
                items.append(
                    {
                        "type": "ACCESSORY_SALE",
                        "object_id": row["id"],
                        "amount": row["total_price"],
                        "profit": row["profit"],
                        "occurred_at": row["sold_at"],
                    }
                )

        if role_scope == "FULL":
            if expenses_qs is None:
                expenses_qs = Expense.objects.filter(branch=branch, is_deleted=False).select_related(
                    "created_by",
                    "branch",
                )
            expense_rows = expenses_qs.filter(
                added_at__gte=start_date,
                added_at__lt=end_date,
            ).values("id", "amount", "type", "added_at").order_by("-added_at")[:20]
            for row in expense_rows:
                items.append(
                    {
                        "type": "EXPENSE",
                        "object_id": row["id"],
                        "amount": row["amount"],
                        "meta": {"expense_type": row["type"]},
                        "occurred_at": row["added_at"],
                    }
                )

            if salary_qs is None:
                salary_qs = Salary.objects.filter(branch=branch, is_deleted=False).select_related(
                    "created_by",
                    "branch",
                )
            salary_rows = salary_qs.filter(
                added_at__gte=start_date,
                added_at__lt=end_date,
            ).values("id", "amount", "added_at").order_by("-added_at")[:20]
            for row in salary_rows:
                items.append(
                    {
                        "type": "SALARY",
                        "object_id": row["id"],
                        "amount": row["amount"],
                        "occurred_at": row["added_at"],
                    }
                )

            if extra_profit_qs is None:
                extra_profit_qs = ExtraProfit.objects.filter(branch=branch, is_deleted=False)
            extra_rows = extra_profit_qs.filter(
                added_at__gte=start_date,
                added_at__lt=end_date,
            ).values("id", "amount", "added_at").order_by("-added_at")[:20]
            for row in extra_rows:
                items.append(
                    {
                        "type": "EXTRA_PROFIT",
                        "object_id": row["id"],
                        "amount": row["amount"],
                        "occurred_at": row["added_at"],
                    }
                )

            if payments_qs is None:
                payments_qs = DebtPayment.objects.filter(
                    debt__branch=branch,
                    debt__is_deleted=False,
                    is_deleted=False,
                )
            payments_qs = filter_payments_by_debt_month(payments_qs, start_date)
            payment_rows = payments_qs.filter(
                added_at__gte=start_date,
                added_at__lt=end_date,
            ).values("id", "amount", "added_at").order_by("-added_at")[:20]
            for row in payment_rows:
                items.append(
                    {
                        "type": "DEBT_PAYMENT",
                        "object_id": row["id"],
                        "amount": row["amount"],
                        "occurred_at": row["added_at"],
                    }
                )

        items.sort(key=lambda item: item["occurred_at"], reverse=True)
        return items[:20]

    @staticmethod
    def _build_branch_dashboard_live(
        branch,
        *,
        year=None,
        month=None,
        seller_id=None,
        role_scope="FULL",
        user=None,
        start_date=None,
        end_date=None,
    ):
        start_date, end_date = _resolve_period_with_override(year, month, start_date, end_date)
        phones_qs = Phone.objects.filter(branch=branch, is_deleted=False).select_related(
            "branch",
            "sold_by",
        )
        accessory_sales_qs = AccessorySale.objects.filter(branch=branch).select_related(
            "branch",
            "sold_by",
            "accessory",
        )
        debts_qs = Debt.objects.filter(branch=branch, is_deleted=False).select_related(
            "created_by",
            "branch",
        )
        expenses_qs = Expense.objects.filter(branch=branch, is_deleted=False).select_related(
            "created_by",
            "branch",
        )
        salary_qs = Salary.objects.filter(branch=branch, is_deleted=False).select_related(
            "created_by",
            "branch",
        )
        payments_qs = DebtPayment.objects.filter(
            debt__branch=branch,
            debt__is_deleted=False,
            is_deleted=False,
        )
        extra_profit_qs = ExtraProfit.objects.filter(branch=branch, is_deleted=False)

        phone_capital = {"invested_amount": 0, "current_balance": 0}
        accessory_capital = {"invested_amount": 0, "current_balance": 0}
        debt_summary = {
            "total_we_gave": 0,
            "total_we_took": 0,
            "remaining_we_gave": 0,
            "remaining_we_took": 0,
        }
        expense_summary = {"shop_expense_total": 0, "employee_expense_total": 0}
        salary_summary = {"salary_total": 0}

        if role_scope in {"FULL", "PHONE_ONLY"}:
            phone_capital = DashboardService.get_phone_capital_summary(
                branch,
                year=year,
                month=month,
                user=user,
                start_date=start_date,
                end_date=end_date,
            )
        if role_scope in {"FULL", "ACCESSORY_ONLY"}:
            accessory_capital = DashboardService.get_accessory_capital_summary(
                branch,
                year=year,
                month=month,
                user=user,
                start_date=start_date,
                end_date=end_date,
            )
        if role_scope == "FULL":
            debt_summary = DashboardService.get_debt_summary(
                branch,
                year=year,
                month=month,
                role_scope=role_scope,
                start_date=start_date,
                end_date=end_date,
                debts_qs=debts_qs,
            )
            expense_summary = DashboardService.get_expense_summary(
                branch,
                year=year,
                month=month,
                role_scope=role_scope,
                start_date=start_date,
                end_date=end_date,
                expenses_qs=expenses_qs,
            )
            salary_summary = DashboardService.get_salary_summary(
                branch,
                year=year,
                month=month,
                role_scope=role_scope,
                start_date=start_date,
                end_date=end_date,
                salary_qs=salary_qs,
            )

        profit_summary = DashboardService.get_profit_summary(
            branch,
            year=year,
            month=month,
            seller_id=seller_id,
            role_scope=role_scope,
            start_date=start_date,
            end_date=end_date,
            phones_qs=phones_qs,
            accessory_sales_qs=accessory_sales_qs,
            extra_profit_qs=extra_profit_qs,
        )
        inventory_summary = DashboardService.get_inventory_summary(
            branch,
            year=year,
            month=month,
            seller_id=seller_id,
            role_scope=role_scope,
            start_date=start_date,
            end_date=end_date,
            phones_qs=phones_qs,
            accessory_sales_qs=accessory_sales_qs,
        )
        last_transactions = DashboardService.get_last_transactions(
            branch,
            year=year,
            month=month,
            seller_id=seller_id,
            role_scope=role_scope,
            start_date=start_date,
            end_date=end_date,
            phones_qs=phones_qs,
            accessory_sales_qs=accessory_sales_qs,
            expenses_qs=expenses_qs,
            salary_qs=salary_qs,
            extra_profit_qs=extra_profit_qs,
            payments_qs=payments_qs,
        )

        result = {
            "phone_capital": phone_capital,
            "accessory_capital": accessory_capital,
            "debt_summary": debt_summary,
            "expense_summary": expense_summary,
            "salary_summary": salary_summary,
            "profit_summary": profit_summary,
            "inventory_summary": inventory_summary,
            "last_transactions": last_transactions,
        }
        return result

    @staticmethod
    def get_branch_dashboard(
        branch,
        year=None,
        month=None,
        seller_id=None,
        role_scope="FULL",
        user=None,
        start_date=None,
        end_date=None,
    ):
        start_date, end_date, month_start = DashboardService._resolve_month_period(
            year,
            month,
            start_date,
            end_date,
        )
        can_use_snapshot = seller_id is None and role_scope == "FULL" and user is None
        if not DashboardService._is_current_month(month_start):
            if can_use_snapshot:
                snapshot = DashboardService._get_dashboard_snapshot(branch, month_start)
                if snapshot is not None:
                    return DashboardService._with_snapshot_metadata(
                        snapshot.dashboard_data,
                        snapshot=snapshot,
                    )
                live_data = DashboardService._build_branch_dashboard_live(
                    branch,
                    year=year,
                    month=month,
                    seller_id=seller_id,
                    role_scope=role_scope,
                    user=user,
                    start_date=start_date,
                    end_date=end_date,
                )
                return DashboardService._with_snapshot_metadata(
                    live_data,
                    month_start=month_start,
                )

            return DashboardService._build_branch_dashboard_live(
                branch,
                year=year,
                month=month,
                seller_id=seller_id,
                role_scope=role_scope,
                user=user,
                start_date=start_date,
                end_date=end_date,
            )

        cache_key = _dashboard_cache_key(
            "branch",
            branch.id,
            year or start_date.year,
            month or start_date.month,
            role_scope,
            seller_id or "all",
            getattr(user, "id", None) or "no-user",
        )
        cached = cache.get(cache_key)
        if cached is not None:
            return cached

        result = DashboardService._build_branch_dashboard_live(
            branch,
            year=year,
            month=month,
            seller_id=seller_id,
            role_scope=role_scope,
            user=user,
            start_date=start_date,
            end_date=end_date,
        )
        cache.set(cache_key, result, 30)
        return result

    @staticmethod
    def _build_phone_dashboard_live(
        branch,
        *,
        year=None,
        month=None,
        start_date=None,
        end_date=None,
    ):
        start_date, end_date = _resolve_period_with_override(year, month, start_date, end_date)

        phone_capital = DashboardService.get_phone_capital_summary(
            branch=branch,
            year=year,
            month=month,
            start_date=start_date,
            end_date=end_date,
        )
        invested_amount = phone_capital.get("invested_amount") or 0
        current_balance = phone_capital.get("current_balance") or 0

        phone_sales_qs = Phone.objects.filter(
            branch=branch,
            is_deleted=False,
            is_sold=True,
            sold_at__gte=start_date,
            sold_at__lt=end_date,
        )
        phone_sales_totals = phone_sales_qs.aggregate(
            total_sell=Sum("sell_price"),
            total_cost=Sum("cost_price"),
            total_count=Count("id"),
        )
        phone_profit = (phone_sales_totals["total_sell"] or 0) - (
            phone_sales_totals["total_cost"] or 0
        )

        extra_profit = DashboardService.get_extra_profit_summary(
            branch=branch,
            year=year,
            month=month,
            role_scope="PHONE_ONLY",
            start_date=start_date,
            end_date=end_date,
        ).get("extra_profit") or 0

        expense_summary = DashboardService.get_expense_summary(
            branch=branch,
            year=year,
            month=month,
            role_scope="PHONE_ONLY",
            start_date=start_date,
            end_date=end_date,
        )
        debt_summary = DashboardService.get_debt_summary(
            branch=branch,
            year=year,
            month=month,
            role_scope="PHONE_ONLY",
            start_date=start_date,
            end_date=end_date,
        )
        payment_summary = DashboardService.get_debt_payment_summary(
            branch=branch,
            year=year,
            month=month,
            role_scope="PHONE_ONLY",
            start_date=start_date,
            end_date=end_date,
        )

        phones_bought_qs = Phone.objects.filter(
            branch=branch,
            is_deleted=False,
            added_at__gte=start_date,
            added_at__lt=end_date,
        )
        phones_bought_totals = phones_bought_qs.aggregate(
            total=Sum("cost_price"),
            total_count=Count("id"),
        )

        phones_remaining_qs = Phone.objects.filter(
            branch=branch,
            is_deleted=False,
            is_sold=False,
            is_month_closed=False,
        )
        phones_remaining_totals = phones_remaining_qs.aggregate(
            total=Sum("cost_price"),
            total_count=Count("id"),
        )

        sales_series = list(
            phone_sales_qs.annotate(day=ExtractDay("sold_at"))
            .values("day")
            .annotate(amount=Sum("sell_price"))
            .order_by("day")
        )

        net_profit = phone_profit + extra_profit

        return {
            "invested_amount": invested_amount,
            "current_balance": current_balance,
            "phone_profit": phone_profit,
            "extra_profit": extra_profit,
            "net_profit": net_profit,
            "total_expense": expense_summary.get("total_expense") or 0,
            "shop_expense": expense_summary.get("shop_expense_total") or 0,
            "employee_expense": expense_summary.get("employee_expense_total") or 0,
            "store_owes": debt_summary.get("remaining_we_took") or 0,
            "others_owe": debt_summary.get("remaining_we_gave") or 0,
            "debt_paid": payment_summary.get("debt_paid") or 0,
            "debt_returned": payment_summary.get("debt_returned") or 0,
            "phones_bought_count": phones_bought_totals.get("total_count") or 0,
            "phones_sold_count": phone_sales_totals.get("total_count") or 0,
            "phones_remaining_count": phones_remaining_totals.get("total_count") or 0,
            "total_cost_bought": phones_bought_totals.get("total") or 0,
            "total_sold_value": phone_sales_totals.get("total_sell") or 0,
            "remaining_value": phones_remaining_totals.get("total") or 0,
            "sales_series": sales_series,
        }

    @staticmethod
    def get_phone_dashboard(
        branch,
        year=None,
        month=None,
        start_date=None,
        end_date=None,
    ):
        start_date, end_date, month_start = DashboardService._resolve_month_period(
            year,
            month,
            start_date,
            end_date,
        )
        if not DashboardService._is_current_month(month_start):
            snapshot = DashboardService._get_dashboard_snapshot(branch, month_start)
            if snapshot is not None:
                return DashboardService._with_snapshot_metadata(
                    snapshot.phone_data,
                    snapshot=snapshot,
                )
            live_data = DashboardService._build_phone_dashboard_live(
                branch,
                year=year,
                month=month,
                start_date=start_date,
                end_date=end_date,
            )
            return DashboardService._with_snapshot_metadata(
                live_data,
                month_start=month_start,
            )

        cache_key = _dashboard_cache_key(
            "phone",
            branch.id,
            year or start_date.year,
            month or start_date.month,
        )
        cached = cache.get(cache_key)
        if cached is not None:
            return cached

        result = DashboardService._build_phone_dashboard_live(
            branch,
            year=year,
            month=month,
            start_date=start_date,
            end_date=end_date,
        )
        cache.set(cache_key, result, 30)
        return result

    @staticmethod
    def _build_accessory_dashboard_live(
        branch,
        *,
        year=None,
        month=None,
        role_scope=None,
        start_date=None,
        end_date=None,
    ):
        start_date, end_date = _resolve_period_with_override(year, month, start_date, end_date)
        month_start = start_date.date()

        capital = AccessoryCapital.objects.filter(
            branch=branch,
            month=month_start,
            is_deleted=False,
        ).first()
        invested_amount = capital.invested_amount if capital else 0
        current_balance = capital.current_balance if capital else 0

        sales_qs = AccessorySale.objects.filter(
            branch=branch,
            sold_at__gte=start_date,
            sold_at__lt=end_date,
        ).select_related("branch", "sold_by", "accessory")
        sales_totals = sales_qs.aggregate(
            accessory_profit=Sum("profit"),
            total_sold_value=Sum("total_price"),
            total_quantity_sold=Sum("quantity"),
        )
        accessory_profit = sales_totals.get("accessory_profit") or 0
        total_sold_value = sales_totals.get("total_sold_value") or 0
        total_quantity_sold = sales_totals.get("total_quantity_sold") or 0

        expense_qs = Expense.objects.filter(
            branch=branch,
            is_deleted=False,
            added_at__gte=start_date,
            added_at__lt=end_date,
        ).select_related("created_by", "branch")
        expense_qs = _apply_role_scope_filter(expense_qs, branch, role_scope, user_field="created_by")
        expense_totals = expense_qs.aggregate(
            total_expense=Sum("amount"),
            shop_expense=Sum("amount", filter=Q(type="SHOP_EXPENSE")),
            employee_expense=Sum("amount", filter=Q(type="EMPLOYEE_EXPENSE")),
        )
        total_expense = expense_totals.get("total_expense") or 0
        shop_expense = expense_totals.get("shop_expense") or 0
        employee_expense = expense_totals.get("employee_expense") or 0

        debt_qs = Debt.objects.filter(
            branch=branch,
            is_deleted=False,
            remaining_amount__gt=0,
        ).select_related("created_by", "branch")
        debt_qs = filter_debts_for_month(debt_qs, start_date)
        debt_qs = _apply_role_scope_filter(debt_qs, branch, role_scope, user_field="created_by")
        debt_qs = _apply_debt_domain_scope_filter(debt_qs, role_scope, field_name="domain")
        debt_totals = debt_qs.aggregate(
            store_owes=Coalesce(
                Sum("remaining_amount", filter=Q(direction="WE_TOOK")),
                _decimal_zero(),
            ),
            others_owe=Coalesce(
                Sum("remaining_amount", filter=Q(direction="WE_GAVE")),
                _decimal_zero(),
            ),
        )
        store_owes = debt_totals.get("store_owes")
        others_owe = debt_totals.get("others_owe")

        payment_qs = DebtPayment.objects.filter(
            debt__branch=branch,
            debt__is_deleted=False,
            is_deleted=False,
            added_at__gte=start_date,
            added_at__lt=end_date,
        )
        payment_qs = filter_payments_by_debt_month(payment_qs, start_date)
        payment_qs = _apply_role_scope_filter(payment_qs, branch, role_scope, user_field="paid_by")
        payment_qs = _apply_debt_domain_scope_filter(
            payment_qs,
            role_scope,
            field_name="debt__domain",
        )
        payment_totals = payment_qs.aggregate(
            debt_paid=Sum("amount", filter=Q(debt__direction="WE_TOOK")),
            debt_returned=Sum("amount", filter=Q(debt__direction="WE_GAVE")),
        )
        debt_paid = payment_totals.get("debt_paid") or 0
        debt_returned = payment_totals.get("debt_returned") or 0

        accessory_qs = Accessory.objects.filter(branch=branch, is_deleted=False)
        inventory_value_expr = ExpressionWrapper(
            F("stock") * F("unit_cost"),
            output_field=DecimalField(max_digits=18, decimal_places=2),
        )
        inventory_totals = accessory_qs.aggregate(
            total_accessory_types=Count("id"),
            total_stock=Sum("stock"),
            total_inventory_value=Sum(inventory_value_expr),
        )
        total_accessory_types = inventory_totals.get("total_accessory_types") or 0
        total_stock = inventory_totals.get("total_stock") or 0
        total_inventory_value = inventory_totals.get("total_inventory_value") or 0

        sales_series = list(
            sales_qs.annotate(day=ExtractDay("sold_at"))
            .values("day")
            .annotate(amount=Sum("total_price"))
            .order_by("day")
        )

        result = {
            "invested_amount": invested_amount,
            "current_balance": current_balance,
            "accessory_profit": accessory_profit,
            "total_expense": total_expense,
            "shop_expense": shop_expense,
            "employee_expense": employee_expense,
            "store_owes": store_owes,
            "others_owe": others_owe,
            "debt_paid": debt_paid,
            "debt_returned": debt_returned,
            "total_accessory_types": total_accessory_types,
            "total_stock": total_stock,
            "total_inventory_value": total_inventory_value,
            "total_sold_value": total_sold_value,
            "total_quantity_sold": total_quantity_sold,
            "remaining_stock_value": total_inventory_value,
            "sales_series": sales_series,
        }
        return result

    @staticmethod
    def get_accessory_dashboard(
        branch,
        year=None,
        month=None,
        role_scope=None,
        start_date=None,
        end_date=None,
    ):
        start_date, end_date, month_start = DashboardService._resolve_month_period(
            year,
            month,
            start_date,
            end_date,
        )
        if not DashboardService._is_current_month(month_start):
            snapshot = DashboardService._get_dashboard_snapshot(branch, month_start)
            if snapshot is not None:
                return DashboardService._with_snapshot_metadata(
                    DashboardService._get_accessory_snapshot_data(snapshot, role_scope),
                    snapshot=snapshot,
                )
            live_data = DashboardService._build_accessory_dashboard_live(
                branch,
                year=year,
                month=month,
                role_scope=role_scope,
                start_date=start_date,
                end_date=end_date,
            )
            return DashboardService._with_snapshot_metadata(
                live_data,
                month_start=month_start,
            )

        cache_key = _dashboard_cache_key(
            "accessory",
            branch.id,
            year or start_date.year,
            month or start_date.month,
            role_scope or "FULL",
        )
        cached = cache.get(cache_key)
        if cached is not None:
            return cached

        result = DashboardService._build_accessory_dashboard_live(
            branch,
            year=year,
            month=month,
            role_scope=role_scope,
            start_date=start_date,
            end_date=end_date,
        )
        cache.set(cache_key, result, 30)
        return result

    @staticmethod
    def build_month_snapshot(branch, month):
        month_start = month.replace(day=1)
        start_date, end_date = DashboardService.resolve_period(month_start.year, month_start.month)

        dashboard_data = DashboardService._build_branch_dashboard_live(
            branch,
            year=month_start.year,
            month=month_start.month,
            role_scope="FULL",
            start_date=start_date,
            end_date=end_date,
        )
        phone_data = DashboardService._build_phone_dashboard_live(
            branch,
            year=month_start.year,
            month=month_start.month,
            start_date=start_date,
            end_date=end_date,
        )
        accessory_data = {
            "FULL": DashboardService._build_accessory_dashboard_live(
                branch,
                year=month_start.year,
                month=month_start.month,
                role_scope="FULL",
                start_date=start_date,
                end_date=end_date,
            ),
            "ACCESSORY_ONLY": DashboardService._build_accessory_dashboard_live(
                branch,
                year=month_start.year,
                month=month_start.month,
                role_scope="ACCESSORY_ONLY",
                start_date=start_date,
                end_date=end_date,
            ),
        }
        debt_data = DashboardService.get_debt_summary(
            branch,
            year=month_start.year,
            month=month_start.month,
            role_scope="FULL",
            start_date=start_date,
            end_date=end_date,
        )
        expense_data = DashboardService.get_expense_summary(
            branch,
            year=month_start.year,
            month=month_start.month,
            role_scope="FULL",
            start_date=start_date,
            end_date=end_date,
        )
        salary_data = DashboardService.get_salary_summary(
            branch,
            year=month_start.year,
            month=month_start.month,
            role_scope="FULL",
            start_date=start_date,
            end_date=end_date,
        )
        capital_data = {
            "phone_capital": DashboardService.get_phone_capital_summary(
                branch=branch,
                year=month_start.year,
                month=month_start.month,
                start_date=start_date,
                end_date=end_date,
            ),
            "accessory_capital": DashboardService.get_accessory_capital_summary(
                branch=branch,
                year=month_start.year,
                month=month_start.month,
                start_date=start_date,
                end_date=end_date,
            ),
        }

        return json_safe(
            {
                "dashboard_data": dashboard_data,
                "phone_data": phone_data,
                "accessory_data": accessory_data,
                "debt_data": debt_data,
                "expense_data": expense_data,
                "salary_data": salary_data,
                "capital_data": capital_data,
            }
        )

    @staticmethod
    def build_month_snapshot_with_old_close_month_repair(branch, month):
        payload = DashboardService.build_month_snapshot(branch, month)
        repair_matches = DashboardService.get_old_close_month_phone_repair_matches(branch, month)
        repair_summary = DashboardService._apply_old_close_month_phone_repair(
            payload,
            month,
            repair_matches,
        )
        return payload, repair_summary

    @staticmethod
    def get_owner_branches(owner):
        return [{"id": branch.id, "name": branch.name} for branch in get_owner_branches(owner)]

    @staticmethod
    def get_branch_employees(branch):
        records = (
            BranchUser.objects.filter(branch=branch, is_deleted=False)
            .select_related("user")
            .order_by("-added_at")
        )
        seen = set()
        results = []
        for item in records:
            if item.user_id in seen:
                continue
            seen.add(item.user_id)
            results.append(
                {
                    "id": item.user_id,
                    "username": item.user.username,
                    "role": item.role,
                }
            )
        return results

    @staticmethod
    def get_admin_dashboard():
        current_year, current_month = DashboardService.get_current_year_month()
        cache_key = _dashboard_cache_key("admin", f"{current_year:04d}-{current_month:02d}")
        cached = cache.get(cache_key)
        if cached is not None:
            return cached

        total_branches = Branch.objects.count()
        total_users = CustomUser.objects.filter(is_deleted=False).count()

        status_rows = (
            CustomUser.objects.filter(is_deleted=False)
            .values("account_status")
            .annotate(count=Count("id"))
            .order_by()
        )
        status_counts = {row["account_status"]: row["count"] for row in status_rows}
        active_users = status_counts.get("active", 0)
        grace_users = status_counts.get("grace", 0)
        blocked_users = status_counts.get("blocked", 0)
        vip_users = status_counts.get("vip", 0)

        start_date, end_date = DashboardService.resolve_period(current_year, current_month)
        subscription_income = _sum_or_zero(
            Payment.objects.filter(added_at__gte=start_date, added_at__lt=end_date),
            "amount",
        )

        unpaid_users_count = CustomUser.objects.filter(is_deleted=False, balance__lt=0).count()
        last_payments = list(
            Payment.objects.filter(is_deleted=False)
            .select_related("user")
            .order_by("-added_at")
            .values("id", "user_id", "user__username", "amount", "payment_type", "added_at")[:20]
        )

        result = {
            "total_branches": total_branches,
            "total_users": total_users,
            "active_users": active_users,
            "grace_users": grace_users,
            "blocked_users": blocked_users,
            "vip_users": vip_users,
            "subscription_income_this_month": subscription_income,
            "unpaid_users_count": unpaid_users_count,
            "monthly_income_series": DashboardService.get_monthly_income_series(),
            "user_status_distribution": DashboardService.get_user_status_pie(),
            "last_payments": last_payments,
        }
        cache.set(cache_key, result, 30)
        return result

    @staticmethod
    def get_cashier_dashboard():
        current_year, current_month = DashboardService.get_current_year_month()
        cache_key = _dashboard_cache_key("cashier", f"{current_year:04d}-{current_month:02d}")
        cached = cache.get(cache_key)
        if cached is not None:
            return cached

        total_branches = Branch.objects.count()
        total_users = CustomUser.objects.filter(is_deleted=False).count()
        active_users = CustomUser.objects.filter(is_deleted=False, account_status="active").count()
        blocked_users = CustomUser.objects.filter(is_deleted=False, account_status="blocked").count()

        start_date, end_date = DashboardService.resolve_period(current_year, current_month)
        payments_this_month = _sum_or_zero(
            Payment.objects.filter(added_at__gte=start_date, added_at__lt=end_date),
            "amount",
        )

        last_payments = list(
            Payment.objects.filter(is_deleted=False)
            .select_related("user")
            .order_by("-added_at")
            .values("id", "user_id", "user__username", "amount", "payment_type", "added_at")[:20]
        )

        result = {
            "total_branches": total_branches,
            "total_users": total_users,
            "active_users": active_users,
            "blocked_users": blocked_users,
            "payments_this_month": payments_this_month,
            "last_payments": last_payments,
        }
        cache.set(cache_key, result, 30)
        return result

    @staticmethod
    def get_monthly_income_series():
        current_year, current_month = DashboardService.get_current_year_month()
        months = _months_back(current_year, current_month, 12)
        start_year, start_month = months[0]
        start_date = _make_aware(datetime(start_year, start_month, 1))
        _, end_date = DashboardService.resolve_period(current_year, current_month)

        rows = (
            Payment.objects.filter(added_at__gte=start_date, added_at__lt=end_date)
            .annotate(month=TruncMonth("added_at"))
            .values("month")
            .annotate(amount=Sum("amount"))
            .order_by("month")
        )
        amount_map = {(row["month"].year, row["month"].month): row["amount"] for row in rows}
        series = []
        for year, month in months:
            series.append({"month": month, "amount": amount_map.get((year, month)) or 0})
        return series

    @staticmethod
    def get_user_status_pie():
        qs = (
            CustomUser.objects.filter(is_deleted=False)
            .values("account_status")
            .annotate(count=Count("id"))
            .order_by()
        )
        counts = {row["account_status"]: row["count"] for row in qs}
        return [
            {"status": "active", "count": counts.get("active", 0)},
            {"status": "grace", "count": counts.get("grace", 0)},
            {"status": "blocked", "count": counts.get("blocked", 0)},
            {"status": "vip", "count": counts.get("vip", 0)},
        ]

    # ------------------------------------------------------------------
    # Comparison / analytics helpers
    # ------------------------------------------------------------------

    @staticmethod
    def get_previous_month(year, month):
        if month == 1:
            return year - 1, 12
        return year, month - 1

    @staticmethod
    def compare_metric(current, other, *, mode="previous"):
        """
        Return a JSON-safe comparison dict.

        mode="previous" → includes "previous" key.
        mode="alltime"  → includes "average" key.

        Rules:
        - direction: "up" | "down" | "neutral"
        - percent: float rounded to 2 dp, or None when denominator is 0
          and numerator is nonzero ("Yangi" case).
        - If both values are 0: direction="neutral", percent=0.
        """
        try:
            current = Decimal(str(current or 0))
            other = Decimal(str(other or 0))
        except Exception:
            current = Decimal("0")
            other = Decimal("0")

        diff = current - other

        if other == 0 and current > 0:
            direction = "up"
            percent = None
        elif other == 0 and current < 0:
            direction = "down"
            percent = None
        elif other == 0:
            direction = "neutral"
            percent = 0
        else:
            percent = round(float(diff / other * 100), 2)
            direction = "up" if diff > 0 else ("down" if diff < 0 else "neutral")

        result = {
            "current": "{:.2f}".format(float(current)),
            "diff": "{:.2f}".format(float(diff)),
            "percent": percent,
            "direction": direction,
        }
        if mode == "previous":
            result["previous"] = "{:.2f}".format(float(other))
        else:
            result["average"] = "{:.2f}".format(float(other))
        return result

    @staticmethod
    def get_phone_dashboard_comparison(branch, year, month, current_data=None):
        """Build previous-month and all-time comparison for the phone dashboard."""
        if current_data is None:
            current_data = DashboardService.get_phone_dashboard(branch, year, month)

        cur_sold = current_data.get("total_sold_value") or 0
        cur_profit = current_data.get("phone_profit") or 0
        cur_net = current_data.get("net_profit") or 0
        cur_count = current_data.get("phones_sold_count") or 0

        prev_year, prev_month = DashboardService.get_previous_month(year, month)
        prev_data = DashboardService.get_phone_dashboard(branch, prev_year, prev_month)
        prev_sold = prev_data.get("total_sold_value") or 0
        prev_profit = prev_data.get("phone_profit") or 0
        prev_net = prev_data.get("net_profit") or 0
        prev_count = prev_data.get("phones_sold_count") or 0

        # All-time: monthly aggregates up to and including selected month
        next_month_start = _next_month_date(date(year, month, 1))
        next_month_dt = _make_aware(datetime.combine(next_month_start, datetime.min.time()))

        monthly_rows = list(
            Phone.objects.filter(
                branch=branch, is_deleted=False, is_sold=True, sold_at__lt=next_month_dt,
            )
            .annotate(m=TruncMonth("sold_at"))
            .values("m")
            .annotate(s=Sum("sell_price"), c=Sum("cost_price"), cnt=Count("id"))
            .order_by("m")
        )

        extra_by_month = {
            row["m"]: (row["extra"] or 0)
            for row in (
                ExtraProfit.objects.filter(
                    branch=branch, is_deleted=False, added_at__lt=next_month_dt,
                )
                .filter(
                    Q(created_by__branch_roles__branch=branch)
                    & Q(created_by__branch_roles__is_deleted=False)
                    & (
                        Q(created_by__branch_roles__role="PHONE_SELLER")
                        | Q(created_by__branch_roles__role="OWNER")
                    )
                )
                .distinct()
                .annotate(m=TruncMonth("added_at"))
                .values("m")
                .annotate(extra=Sum("amount"))
            )
        }

        n = len(monthly_rows) or 1
        if monthly_rows:
            sum_sold = sum((r["s"] or 0) for r in monthly_rows)
            sum_profit = sum(((r["s"] or 0) - (r["c"] or 0)) for r in monthly_rows)
            sum_net = sum(
                ((r["s"] or 0) - (r["c"] or 0)) + (extra_by_month.get(r["m"]) or 0)
                for r in monthly_rows
            )
            sum_count = sum((r["cnt"] or 0) for r in monthly_rows)
            avg_sold = Decimal(str(sum_sold)) / n
            avg_profit = Decimal(str(sum_profit)) / n
            avg_net = Decimal(str(sum_net)) / n
            avg_count = Decimal(str(sum_count)) / n
        else:
            avg_sold = avg_profit = avg_net = avg_count = Decimal("0")

        cm = DashboardService.compare_metric
        return {
            "previous_month": {
                "total_sold_value": cm(cur_sold, prev_sold, mode="previous"),
                "phone_profit": cm(cur_profit, prev_profit, mode="previous"),
                "net_profit": cm(cur_net, prev_net, mode="previous"),
                "phones_sold_count": cm(cur_count, prev_count, mode="previous"),
            },
            "all_time": {
                "total_sold_value": cm(cur_sold, avg_sold, mode="alltime"),
                "phone_profit": cm(cur_profit, avg_profit, mode="alltime"),
                "net_profit": cm(cur_net, avg_net, mode="alltime"),
                "phones_sold_count": cm(cur_count, avg_count, mode="alltime"),
            },
        }

    @staticmethod
    def get_accessory_dashboard_comparison(branch, year, month, role_scope=None, current_data=None):
        """Build previous-month and all-time comparison for the accessory dashboard."""
        if current_data is None:
            current_data = DashboardService.get_accessory_dashboard(
                branch, year, month, role_scope
            )

        cur_sold = current_data.get("total_sold_value") or 0
        cur_profit = current_data.get("accessory_profit") or 0
        cur_qty = current_data.get("total_quantity_sold") or 0

        prev_year, prev_month = DashboardService.get_previous_month(year, month)
        prev_data = DashboardService.get_accessory_dashboard(
            branch, prev_year, prev_month, role_scope
        )
        prev_sold = prev_data.get("total_sold_value") or 0
        prev_profit = prev_data.get("accessory_profit") or 0
        prev_qty = prev_data.get("total_quantity_sold") or 0

        # All-time: monthly aggregates up to and including selected month
        next_month_start = _next_month_date(date(year, month, 1))
        next_month_dt = _make_aware(datetime.combine(next_month_start, datetime.min.time()))

        monthly_rows = list(
            AccessorySale.objects.filter(branch=branch, sold_at__lt=next_month_dt)
            .annotate(m=TruncMonth("sold_at"))
            .values("m")
            .annotate(sv=Sum("total_price"), ap=Sum("profit"), qty=Sum("quantity"))
            .order_by("m")
        )

        n = len(monthly_rows) or 1
        if monthly_rows:
            avg_sold = Decimal(str(sum((r["sv"] or 0) for r in monthly_rows))) / n
            avg_profit = Decimal(str(sum((r["ap"] or 0) for r in monthly_rows))) / n
            avg_qty = Decimal(str(sum((r["qty"] or 0) for r in monthly_rows))) / n
        else:
            avg_sold = avg_profit = avg_qty = Decimal("0")

        cm = DashboardService.compare_metric
        return {
            "previous_month": {
                "total_sold_value": cm(cur_sold, prev_sold, mode="previous"),
                "accessory_profit": cm(cur_profit, prev_profit, mode="previous"),
                "total_quantity_sold": cm(cur_qty, prev_qty, mode="previous"),
            },
            "all_time": {
                "total_sold_value": cm(cur_sold, avg_sold, mode="alltime"),
                "accessory_profit": cm(cur_profit, avg_profit, mode="alltime"),
                "total_quantity_sold": cm(cur_qty, avg_qty, mode="alltime"),
            },
        }
