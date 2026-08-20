from django.db import transaction
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


class PhoneUpdateService:
    @staticmethod
    def update_phone(phone, validated_data, updated_by):
        if phone.is_month_closed:
            raise ValueError(_("Yopilgan oy telefoni yangilab bo'lmaydi."))
        with transaction.atomic():
            old_data = _snapshot_phone(phone)
            old_cost_price = phone.cost_price
            new_cost_price = validated_data.get("cost_price", old_cost_price)

            if new_cost_price != old_cost_price:
                month_start = _month_start(phone.added_at)
                capital = CapitalService.get_capital_for_user(
                    updated_by,
                    phone.branch,
                    month_start,
                    capital_type="phone",
                )
                difference = old_cost_price - new_cost_price
                if difference > 0:
                    CapitalService.add_balance(capital, difference)
                elif difference < 0:
                    CapitalService.subtract_balance(capital, abs(difference))

            for attr, value in validated_data.items():
                setattr(phone, attr, value)
            phone.save()

            JournalService.log_update(
                user=updated_by,
                instance=phone,
                old_data=old_data,
                new_data=_snapshot_phone(phone),
            )

            return phone
