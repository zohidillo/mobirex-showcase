from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

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


class SalaryCreateService:
    @staticmethod
    def create_salary(validated_data, created_by):
        with transaction.atomic():
            data = dict(validated_data)
            data["created_by"] = created_by
            salary = Salary.objects.create(**data)

            month_start = _month_start(timezone.localtime())
            capital_type = None
            if (
                created_by.is_superuser
                or created_by.is_cashier
                or created_by.has_role("OWNER", salary.branch)
                or getattr(salary.branch, "owner_id", None) == created_by.id
            ):
                capital_type = _resolve_salary_capital_type(salary.employee, salary.branch)
            capital = CapitalService.get_capital_for_user(
                created_by,
                salary.branch,
                month_start,
                capital_type=capital_type,
            )
            CapitalService.subtract_balance(capital, salary.amount)

            JournalService.log_create(
                user=created_by,
                instance=salary,
                new_data=_snapshot(salary),
            )

            return salary
