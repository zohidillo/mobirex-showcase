from django.db import transaction
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from src.services.capital import CapitalService
from src.services.journal import JournalService
from src.shared.json_utils import json_safe


def _month_start(value):
    if hasattr(value, "date"):
        value = value.date()
    return value.replace(day=1)


def _snapshot_phone(phone):
    data = {}
    for field in phone._meta.fields:
        value = getattr(phone, field.attname)
        data[field.attname] = json_safe(value)
    return data


class PhoneSellService:
    @staticmethod
    def sell_phone(phone, sell_price, sold_by):
        if phone.is_month_closed:
            raise ValueError(_("Yopilgan oy telefoni sotib bo'lmaydi."))
        with transaction.atomic():
            old_data = _snapshot_phone(phone)

            phone.sell_price = sell_price
            phone.is_sold = True
            phone.sold_by = sold_by
            phone.sold_at = timezone.now()
            phone.save()

            month_start = _month_start(phone.sold_at)
            capital = CapitalService.get_capital_for_user(
                sold_by,
                phone.branch,
                month_start,
                capital_type="phone",
            )
            CapitalService.add_balance(capital, sell_price)

            JournalService.log_update(
                user=sold_by,
                instance=phone,
                old_data=old_data,
                new_data=_snapshot_phone(phone),
            )

            return phone
