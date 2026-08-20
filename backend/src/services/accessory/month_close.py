import calendar
from datetime import date, datetime, time

from django.db import transaction
from django.utils import timezone

from src.core.models import Accessory, AccessorySale
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


def _snapshot_accessory(accessory):
    data = {}
    for field in accessory._meta.fields:
        value = getattr(accessory, field.attname)
        data[field.attname] = json_safe(value)
    return data


def _snapshot_sale(sale):
    data = {}
    for field in sale._meta.fields:
        value = getattr(sale, field.attname)
        data[field.attname] = json_safe(value)
    return data


class AccessoryMonthCloseService:
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
                capital_type="accessory",
            )
            capital_next = CapitalService.get_capital_for_user(
                performed_by,
                branch,
                next_month_start,
                capital_type="accessory",
            )

            accessories = (
                Accessory.objects.select_for_update()
                .filter(
                    branch=branch,
                    is_deleted=False,
                    stock__gt=0,
                    added_at__date__gte=month_start,
                    added_at__date__lte=month_end,
                )
                .order_by("id")
            )

            for accessory in accessories:
                quantity = accessory.stock
                total = accessory.unit_cost * quantity

                old_accessory_data = _snapshot_accessory(accessory)

                sale = AccessorySale.objects.create(
                    accessory=accessory,
                    branch=branch,
                    quantity=quantity,
                    unit_cost=accessory.unit_cost,
                    total_cost=total,
                    total_price=total,
                    profit=total - total,
                    sold_by=performed_by,
                    sold_at=month_end_dt,
                )

                accessory.stock = 0
                accessory.save()

                CapitalService.add_balance(capital_current, total)

                JournalService.log_create(
                    user=performed_by,
                    instance=sale,
                    new_data=_snapshot_sale(sale),
                )

                JournalService.log_update(
                    user=performed_by,
                    instance=accessory,
                    old_data=old_accessory_data,
                    new_data=_snapshot_accessory(accessory),
                )

                new_accessory = Accessory.objects.create(
                    name=accessory.name,
                    category=accessory.category,
                    branch=accessory.branch,
                    unit_cost=accessory.unit_cost,
                    stock=quantity,
                    image=accessory.image,
                    added_by=accessory.added_by,
                    is_active=accessory.is_active,
                )
                Accessory.objects.filter(pk=new_accessory.pk).update(
                    added_at=next_month_start_dt
                )
                new_accessory.added_at = next_month_start_dt

                capital_next.invested_amount = capital_next.invested_amount + total
                capital_next.save()

                JournalService.log_create(
                    user=performed_by,
                    instance=new_accessory,
                    new_data=_snapshot_accessory(new_accessory),
                )

            return accessories
