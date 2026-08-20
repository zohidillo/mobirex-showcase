import calendar
from datetime import date, datetime, time

from django.db import transaction
from django.utils import timezone

from src.core.models import Phone
from src.services.capital import CapitalService
from src.services.journal import JournalService
from src.shared.json_utils import json_safe


def _month_start(value):
    if hasattr(value, "date"):
        value = value.date()
    return value.replace(day=1)


def _month_end(value):
    if hasattr(value, "date"):
        value = value.date()
    last_day = calendar.monthrange(value.year, value.month)[1]
    return date(value.year, value.month, last_day)


def _next_month_start(value):
    value = _month_start(value)
    year = value.year
    month = value.month
    if month == 12:
        return date(year + 1, 1, 1)
    return date(year, month + 1, 1)


def _aware_start(value):
    dt = datetime.combine(value, time.min)
    if timezone.is_naive(dt):
        return timezone.make_aware(dt)
    return dt


def _aware_end(value):
    dt = datetime.combine(value, time.max).replace(microsecond=0)
    if timezone.is_naive(dt):
        return timezone.make_aware(dt)
    return dt


def _snapshot_phone(phone):
    data = {}
    for field in phone._meta.fields:
        value = getattr(phone, field.attname)
        data[field.attname] = json_safe(value)
    return data


class PhoneMonthCloseService:
    @staticmethod
    def close_month(branch, month, performed_by):
        with transaction.atomic():
            month_start = _month_start(month)
            month_end = _month_end(month_start)
            next_month_start = _next_month_start(month_start)

            month_end_dt = _aware_end(month_end)
            next_month_start_dt = _aware_start(next_month_start)

            capital_current = CapitalService.get_capital_for_user(
                performed_by,
                branch,
                month_start,
                capital_type="phone",
            )
            capital_next = CapitalService.get_capital_for_user(
                performed_by,
                branch,
                next_month_start,
                capital_type="phone",
            )

            phones = (
                Phone.objects.select_for_update()
                .filter(
                    branch=branch,
                    is_sold=False,
                    is_deleted=False,
                    added_at__date__gte=month_start,
                    added_at__date__lte=month_end,
                )
                .order_by("id")
            )

            for phone in phones:
                old_data = _snapshot_phone(phone)

                phone.sell_price = phone.cost_price
                phone.is_sold = True
                phone.sold_by = performed_by
                phone.sold_at = month_end_dt
                phone.save()

                CapitalService.add_balance(capital_current, phone.cost_price)

                JournalService.log_update(
                    user=performed_by,
                    instance=phone,
                    old_data=old_data,
                    new_data=_snapshot_phone(phone),
                )

                new_phone = Phone.objects.create(
                    name=phone.name,
                    category=phone.category,
                    branch=phone.branch,
                    imei=phone.imei,
                    storage=phone.storage,
                    color=phone.color,
                    from_by=phone.from_by,
                    cost_price=phone.cost_price,
                    sell_price=None,
                    is_sold=False,
                    added_by=phone.added_by,
                    sold_by=None,
                    sold_at=None,
                )
                Phone.objects.filter(pk=new_phone.pk).update(added_at=next_month_start_dt)
                new_phone.added_at = next_month_start_dt

                CapitalService.subtract_balance(capital_next, phone.cost_price)

                JournalService.log_create(
                    user=performed_by,
                    instance=new_phone,
                    new_data=_snapshot_phone(new_phone),
                )

            return phones
