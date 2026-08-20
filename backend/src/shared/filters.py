import logging
from datetime import datetime, time, timedelta

from django.db.models.functions import ExtractYear
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


logger = logging.getLogger(__name__)


MONTH_CHOICES = (
    (1, _("Yanvar")),
    (2, _("Fevral")),
    (3, _("Mart")),
    (4, _("Aprel")),
    (5, _("May")),
    (6, _("Iyun")),
    (7, _("Iyul")),
    (8, _("Avgust")),
    (9, _("Sentabr")),
    (10, _("Oktabr")),
    (11, _("Noyabr")),
    (12, _("Dekabr")),
)


def parse_date_input(value):
    """Parse a YYYY-MM-DD string into a date."""
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except (TypeError, ValueError):
        return None


def apply_datetime_range(queryset, *, field_name, from_date=None, to_date=None):
    """Apply an inclusive date range to a datetime field."""
    if from_date:
        start_dt = timezone.make_aware(datetime.combine(from_date, time.min))
        queryset = queryset.filter(**{f"{field_name}__gte": start_dt})
    if to_date:
        end_dt = timezone.make_aware(datetime.combine(to_date + timedelta(days=1), time.min))
        queryset = queryset.filter(**{f"{field_name}__lt": end_dt})
    return queryset


def get_local_now(reference_time=None):
    """Return the current local datetime in the active timezone."""
    if reference_time is None:
        return timezone.localtime()
    if timezone.is_naive(reference_time):
        reference_time = timezone.make_aware(reference_time, timezone.get_current_timezone())
    return timezone.localtime(reference_time)


def get_current_year_month(reference_time=None):
    """Return the current local year and month."""
    now = get_local_now(reference_time)
    return now, now.year, now.month


def normalize_year_month(year=None, month=None, *, default_to_current=True, source=None):
    """Normalize year and month values with an optional current-month fallback."""
    input_year = year
    input_month = month
    now, current_year, current_month = get_current_year_month()

    try:
        year = int(year)
        month = int(month)
    except (TypeError, ValueError):
        year = None
        month = None

    if year is not None and year < 1:
        year = None
    if month is not None and not 1 <= month <= 12:
        month = None

    default_applied = False
    if (not year or not month) and default_to_current:
        year = current_year
        month = current_month
        default_applied = True

    logger.info(
        "Date filter resolved | source=%s now=%s input_year=%s input_month=%s resolved_year=%s resolved_month=%s default_applied=%s",
        source or "unknown",
        now.isoformat(),
        input_year,
        input_month,
        year,
        month,
        default_applied,
    )
    return year, month


def get_request_year_month(request, *, default_to_current=True, source=None):
    """Read and normalize year/month values from request query parameters."""
    params = getattr(request, "GET", None) or getattr(request, "query_params", {}) or {}
    resolved_source = source or getattr(request, "path", None) or "request"
    return normalize_year_month(
        params.get("year"),
        params.get("month"),
        default_to_current=default_to_current,
        source=resolved_source,
    )


def get_default_year_month(request, *, source=None):
    """Return request year/month with a current month fallback."""
    return get_request_year_month(
        request,
        default_to_current=True,
        source=source,
    )


def get_available_years(queryset, date_field="created_at"):
    """Return distinct years present in the queryset for the given date field."""
    current_year = get_local_now().year
    if queryset is None:
        return [current_year]

    queryset = queryset.order_by()
    years = {
        int(year)
        for year in queryset.annotate(_available_year=ExtractYear(date_field)).values_list(
            "_available_year",
            flat=True,
        )
        if year
    }
    if not years:
        return [current_year]
    return sorted(years, reverse=True)


def get_month_bounds(year, month, *, default_to_current=True, source=None):
    """Return aware month start/end datetimes for the given or current month."""
    year, month = normalize_year_month(
        year,
        month,
        default_to_current=default_to_current,
        source=source,
    )
    if year is None or month is None:
        return None, None

    start_dt = timezone.make_aware(datetime(year, month, 1))
    if month == 12:
        end_dt = timezone.make_aware(datetime(year + 1, 1, 1))
    else:
        end_dt = timezone.make_aware(datetime(year, month + 1, 1))
    return start_dt, end_dt


def apply_year_month_filter(
    queryset,
    *,
    field_name,
    year=None,
    month=None,
    default_to_current=False,
    source=None,
):
    """Filter a queryset by the given year and month."""
    start_dt, end_dt = get_month_bounds(
        year,
        month,
        default_to_current=default_to_current,
        source=source or field_name,
    )
    if start_dt is None or end_dt is None:
        return queryset
    return queryset.filter(**{f"{field_name}__gte": start_dt, f"{field_name}__lt": end_dt})


def filter_by_month(
    queryset,
    request,
    field_name,
    *,
    default_to_current=False,
):
    """Filter queryset by request year/month only when values are provided."""
    params = {}
    if request:
        params = getattr(request, "GET", None) or getattr(request, "query_params", {}) or {}

    year = params.get("year")
    month = params.get("month")
    return apply_year_month_filter(
        queryset,
        field_name=field_name,
        year=year,
        month=month,
        default_to_current=default_to_current,
        source=getattr(request, "path", None) or field_name,
    )


def get_filtered_queryset(
    queryset,
    request,
    *,
    field_name="added_at",
    default_to_current=False,
):
    """Backward-compatible wrapper around optional month filtering."""
    return filter_by_month(
        queryset,
        request,
        field_name=field_name,
        default_to_current=default_to_current,
    )
