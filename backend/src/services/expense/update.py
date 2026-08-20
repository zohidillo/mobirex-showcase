from django.core.exceptions import ValidationError
from django.db import transaction

from src.core.models import *
from src.services.capital import CapitalService
from src.services.expense.delete import ExpenseDeleteService
from src.services.journal import JournalService
from src.shared.json_utils import json_safe


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


class ExpenseUpdateService:
    @staticmethod
    def update_expense(expense, validated_data, updated_by):
        with transaction.atomic():
            old_data = _snapshot(expense)
            old_amount = expense.amount
            new_amount = validated_data.get("amount", old_amount)

            if new_amount != old_amount:
                difference = new_amount - old_amount
                month_start = _month_start(expense.added_at)
                capital_type = ExpenseDeleteService._get_capital_type(expense)
                if capital_type == Expense.CAPITAL_TYPE_PHONE:
                    capital = CapitalService.get_phone_capital(expense.branch, month_start)
                else:
                    capital = CapitalService.get_accessory_capital(expense.branch, month_start)
                if difference > 0:
                    CapitalService.subtract_balance(capital, difference)
                elif difference < 0:
                    CapitalService.add_balance(capital, abs(difference))

            for attr, value in validated_data.items():
                setattr(expense, attr, value)
            expense.save()

            JournalService.log_update(
                user=updated_by,
                instance=expense,
                old_data=old_data,
                new_data=_snapshot(expense),
            )

            return expense
