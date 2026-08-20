from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils.translation import gettext_lazy as _

from src.core.models import *
from src.services.capital import CapitalService
from src.services.journal import JournalService
from src.shared.json_utils import json_safe
from src.shared.permissions import get_seller_domain_for_branch


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


class ExpenseCreateService:
    @staticmethod
    def _get_capital_type(user, branch):
        seller_domain = get_seller_domain_for_branch(user, branch)
        if seller_domain == "PHONE":
            return Expense.CAPITAL_TYPE_PHONE
        if seller_domain == "ACCESSORY":
            return Expense.CAPITAL_TYPE_ACCESSORY
        raise ValidationError(_("Faqat sotuvchilar xarajat yaratishi mumkin."))

    @staticmethod
    def create_expense(validated_data, created_by):
        with transaction.atomic():
            data = dict(validated_data)
            capital_type = ExpenseCreateService._get_capital_type(
                created_by,
                data.get("branch"),
            )
            data["created_by"] = created_by
            data["capital_type"] = capital_type
            expense = Expense.objects.create(**data)

            month_start = _month_start(expense.added_at)
            if capital_type == Expense.CAPITAL_TYPE_PHONE:
                capital = CapitalService.get_phone_capital(expense.branch, month_start)
            else:
                capital = CapitalService.get_accessory_capital(expense.branch, month_start)
            CapitalService.subtract_balance(capital, expense.amount)

            JournalService.log_create(
                user=created_by,
                instance=expense,
                new_data=_snapshot(expense),
            )

            return expense
