from django.db import transaction
from django.utils import timezone

from src.core.models import Accessory
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


class AccessoryCreateService:
    @staticmethod
    def create_accessory(validated_data, added_by):
        with transaction.atomic():
            data = dict(validated_data)
            quantity = data.pop("quantity", None)
            if quantity is None:
                quantity = data.get("stock", 0)
            data.pop("stock", None)

            branch = data.get("branch")
            name = data.get("name")
            unit_cost = data.get("unit_cost")

            accessory = (
                Accessory.objects.select_for_update()
                .filter(
                    branch=branch,
                    name=name,
                    unit_cost=unit_cost,
                    is_month_closed=False,
                    is_deleted=False,
                )
                .first()
            )

            if accessory:
                accessory.stock = accessory.stock + quantity
                accessory.save()
            else:
                data["added_by"] = added_by
                data["stock"] = quantity
                accessory = Accessory.objects.create(**data)

            total_cost = accessory.unit_cost * quantity
            month_start = _month_start(timezone.localtime())
            capital = CapitalService.get_capital_for_user(
                added_by,
                accessory.branch,
                month_start,
                capital_type="accessory",
            )
            capital.invested_amount += total_cost
            capital.save()

            JournalService.log_create(
                user=added_by,
                instance=accessory,
                new_data=_snapshot_accessory(accessory),
            )

            return accessory
