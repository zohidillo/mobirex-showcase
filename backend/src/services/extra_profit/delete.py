from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.utils.translation import gettext_lazy as _

from src.core.models import *
from src.services.capital import CapitalService
from src.services.journal import JournalService
from src.shared.json_utils import json_safe
from .policy import can_delete_extra_profit, is_current_month_extra_profit


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


class ExtraProfitDeleteService:
    @staticmethod
    def delete_extra_profit(extra_profit, deleted_by):
        with transaction.atomic():
            extra_profit = (
                ExtraProfit.objects.select_for_update()
                .select_related("branch", "created_by")
                .get(pk=extra_profit.pk)
            )

            if not is_current_month_extra_profit(extra_profit):
                raise ValidationError(_("Qo'shimcha foyda faqat joriy oyda o'chirilishi mumkin."))
            if not can_delete_extra_profit(deleted_by, extra_profit):
                raise PermissionDenied(_("Sizga bu amalni bajarish mumkin emas."))

            old_data = _snapshot(extra_profit)
            month_start = _month_start(extra_profit.added_at)
            capital = CapitalService.get_phone_capital(extra_profit.branch, month_start)
            CapitalService.subtract_balance(capital, extra_profit.amount)

            extra_profit.is_deleted = True
            extra_profit.save()

            JournalService.log_delete(
                user=deleted_by,
                instance=extra_profit,
                old_data=old_data,
            )

            return extra_profit
