from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from src.core.models import *
from src.services.capital import CapitalService
from src.services.journal import JournalService
from src.shared.json_utils import json_safe
from .policy import can_create_extra_profit


def _month_start(value):
    if hasattr(value, "date"):
        value = value.date()
    return value.replace(day=1)


def _snapshot(instance):
    data = {}
    for field in instance._meta.fields:
        value = getattr(instance, field.attname)
        data[field.attname] = json_safe(value)
    return data


class ExtraProfitCreateService:
    @staticmethod
    def create_extra_profit(validated_data, created_by):
        with transaction.atomic():
            data = dict(validated_data)
            branch = data.get("branch")
            if not branch or not can_create_extra_profit(created_by, branch):
                raise PermissionDenied(_("Sizga bu amalni bajarish mumkin emas."))

            month_start = _month_start(timezone.localtime())
            capital = CapitalService.get_phone_capital(branch, month_start)

            data["created_by"] = created_by
            extra_profit = ExtraProfit.objects.create(**data)
            CapitalService.add_balance(capital, extra_profit.amount)

            JournalService.log_create(
                user=created_by,
                instance=extra_profit,
                new_data=_snapshot(extra_profit),
            )

            return extra_profit
