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


def _snapshot_phone(phone):
    data = {}
    for field in phone._meta.fields:
        value = getattr(phone, field.attname)
        data[field.attname] = json_safe(value)
    return data


class PhoneCreateService:
    @staticmethod
    def create_phone(validated_data, added_by):
        with transaction.atomic():
            data = dict(validated_data)
            data["added_by"] = added_by
            if not data.get("branch"):
                branch = None
                if hasattr(added_by, "get_branch"):
                    branch = added_by.get_branch()
                if branch:
                    data["branch"] = branch
            phone = Phone.objects.create(**data)

            month_start = _month_start(timezone.localtime())
            capital = CapitalService.get_capital_for_user(
                added_by,
                phone.branch,
                month_start,
                capital_type="phone",
            )
            CapitalService.subtract_balance(capital, phone.cost_price)

            JournalService.log_create(
                user=added_by,
                instance=phone,
                new_data=_snapshot_phone(phone),
            )

            return phone
