from django.core.exceptions import ValidationError
from django.db import transaction

from src.core.models import *
from src.services.capital import CapitalService
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


def _resolve_salary_capital_type(employee, branch):
    if employee and employee.has_role("ACCESSORY_SELLER", branch):
        return "accessory"
    if employee and employee.has_role("PHONE_SELLER", branch):
        return "phone"
    return "phone"


class SalaryUpdateService:
    @staticmethod
    def update_salary(salary, validated_data, updated_by):
        with transaction.atomic():
            old_data = _snapshot(salary)
            old_amount = salary.amount
            new_amount = validated_data.get("amount", old_amount)

            if new_amount != old_amount:
                difference = new_amount - old_amount
                month_start = _month_start(salary.added_at)
                capital_type = None
                if (
                    updated_by.is_superuser
                    or updated_by.is_cashier
                    or updated_by.has_role("OWNER", salary.branch)
                    or getattr(salary.branch, "owner_id", None) == updated_by.id
                ):
                    capital_type = _resolve_salary_capital_type(salary.employee, salary.branch)
                capital = CapitalService.get_capital_for_user(
                    updated_by,
                    salary.branch,
                    month_start,
                    capital_type=capital_type,
                )
                if difference > 0:
                    CapitalService.subtract_balance(capital, difference)
                elif difference < 0:
                    CapitalService.add_balance(capital, abs(difference))

            for attr, value in validated_data.items():
                setattr(salary, attr, value)
            salary.save()

            JournalService.log_update(
                user=updated_by,
                instance=salary,
                old_data=old_data,
                new_data=_snapshot(salary),
            )

            return salary
