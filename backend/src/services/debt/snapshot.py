from datetime import date, datetime, time
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db.models import DecimalField, F, Max, Q, Sum, Value
from django.db.models.functions import Coalesce
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from src.core.models import Debt, DebtMonthlySnapshot


DECIMAL_OUTPUT_FIELD = DecimalField(max_digits=14, decimal_places=2)


def normalize_month_start(month):
    if month is None:
        month = timezone.localdate()
    if isinstance(month, datetime):
        month = timezone.localdate(month)
    if hasattr(month, "date") and not isinstance(month, date):
        month = month.date()
    if not isinstance(month, date):
        raise ValueError("month must be a date or datetime instance")
    return month.replace(day=1)


def shift_month(month, delta):
    month_start = normalize_month_start(month)
    month_index = month_start.year * 12 + (month_start.month - 1) + delta
    year, month_zero = divmod(month_index, 12)
    return date(year, month_zero + 1, 1)


def get_month_window(month):
    month_start = normalize_month_start(month)
    next_month_start = shift_month(month_start, 1)
    timezone_info = timezone.get_current_timezone()
    month_start_dt = timezone.make_aware(datetime.combine(month_start, time.min), timezone_info)
    next_month_start_dt = timezone.make_aware(
        datetime.combine(next_month_start, time.min),
        timezone_info,
    )
    return month_start, next_month_start, month_start_dt, next_month_start_dt


def is_current_month(month, *, reference_time=None):
    month_start = normalize_month_start(month)
    current_local_date = timezone.localdate(reference_time) if reference_time else timezone.localdate()
    return month_start == current_local_date.replace(day=1)


def get_debt_month_start(debt):
    return normalize_month_start(getattr(debt, "added_at", None))


def filter_queryset_for_month(
    queryset,
    *,
    month=None,
    field_name="added_at",
    default_to_current=False,
):
    if month is None and not default_to_current:
        return queryset
    _, _, month_start_dt, next_month_start_dt = get_month_window(month)
    return queryset.filter(
        **{
            f"{field_name}__gte": month_start_dt,
            f"{field_name}__lt": next_month_start_dt,
        }
    )


def filter_debts_for_month(queryset, month=None, *, default_to_current=False):
    return filter_queryset_for_month(
        queryset,
        month=month,
        field_name="added_at",
        default_to_current=default_to_current,
    )


def filter_payments_by_debt_month(queryset, month=None, *, default_to_current=False):
    return filter_queryset_for_month(
        queryset,
        month=month,
        field_name="debt__added_at",
        default_to_current=default_to_current,
    )


def is_debt_in_current_month(debt, *, reference_time=None):
    return is_current_month(get_debt_month_start(debt), reference_time=reference_time)


def ensure_debt_is_in_current_month(debt, *, message=None, reference_time=None):
    if not is_debt_in_current_month(debt, reference_time=reference_time):
        raise ValidationError(message or _("Faqat joriy oy qarzlari bilan ishlash mumkin."))


def apply_debt_snapshot_to_capital(month, branch, *, force=False):
    target_month = normalize_month_start(month)
    snapshot_month = shift_month(target_month, -1)
    return {
        "applied": False,
        "snapshot_month": snapshot_month,
        "target_month": target_month,
        "phone_adjustment": Decimal("0.00"),
        "accessory_adjustment": Decimal("0.00"),
        "total_adjustment": Decimal("0.00"),
        "force": force,
        "branch_id": getattr(branch, "id", branch),
    }


def generate_debt_snapshot_for_month(month):
    normalize_month_start(month)
    return DebtMonthlySnapshot.objects.none()


def get_closed_debts_queryset(*, queryset=None, month=None):
    total_paid_expression = Coalesce(
        Sum("payments__amount", filter=Q(payments__is_deleted=False)),
        Value(Decimal("0.00")),
        output_field=DECIMAL_OUTPUT_FIELD,
    )

    closed_at_expression = Max(
        "payments__added_at",
        filter=Q(payments__is_deleted=False),
    )

    debts = queryset if queryset is not None else Debt.objects.filter(is_deleted=False)
    if month is not None:
        debts = filter_debts_for_month(debts, month)

    return (
        debts.select_related("branch", "created_by")
        .annotate(total_paid=total_paid_expression, closed_at=closed_at_expression)
        .filter(
            total_paid__gte=F("amount"),
            closed_at__isnull=False,
        )
        .order_by("-closed_at", "-added_at", "-id")
    )


def get_closed_debts_by_month(month, *, queryset=None):
    return get_closed_debts_queryset(queryset=queryset, month=month)
