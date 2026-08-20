from django.db import transaction
from django.utils.translation import gettext_lazy as _

from src.services.capital import CapitalService
from src.services.journal import JournalService
from src.shared.json_utils import json_safe


def _month_start(value):
    if hasattr(value, "date"):
        value = value.date()
    return value.replace(day=1)


def _snapshot_accessory(accessory):
    data = {}
    for field in accessory._meta.fields:
        value = getattr(accessory, field.attname)
        data[field.attname] = json_safe(value)
    return data


class AccessoryUpdateService:
    @staticmethod
    def update_accessory(accessory, validated_data, updated_by):
        if accessory.is_month_closed:
            raise ValueError(_("Yopilgan oy aksessuari yangilab bo'lmaydi."))
        with transaction.atomic():
            old_data = _snapshot_accessory(accessory)
            old_unit_cost = accessory.unit_cost
            new_unit_cost = validated_data.get("unit_cost", old_unit_cost)

            if new_unit_cost != old_unit_cost:
                difference = (new_unit_cost - old_unit_cost) * accessory.stock
                month_start = _month_start(accessory.added_at)
                capital = CapitalService.get_capital_for_user(
                    updated_by,
                    accessory.branch,
                    month_start,
                    capital_type="accessory",
                )
                capital.invested_amount = capital.invested_amount + difference
                capital.save()

            for attr, value in validated_data.items():
                setattr(accessory, attr, value)
            accessory.save()

            JournalService.log_update(
                user=updated_by,
                instance=accessory,
                old_data=old_data,
                new_data=_snapshot_accessory(accessory),
            )

            return accessory
