from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

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


class SalaryDeleteService:
    @staticmethod
    def delete_salary(salary, deleted_by):
        with transaction.atomic():
            now = timezone.localtime()
            salary_added_at = timezone.localtime(salary.added_at)
            if salary_added_at.year != now.year or salary_added_at.month != now.month:
                raise ValidationError(_("Oylik faqat joriy oyda o‘chirilishi mumkin."))

            old_data = _snapshot(salary)
            month_start = _month_start(now)
            capital_type = None
            if (
                deleted_by.is_superuser
                or deleted_by.is_cashier
                or deleted_by.has_role("OWNER", salary.branch)
                or getattr(salary.branch, "owner_id", None) == deleted_by.id
            ):
                capital_type = _resolve_salary_capital_type(salary.employee, salary.branch)
            capital = CapitalService.get_capital_for_user(
                deleted_by,
                salary.branch,
                month_start,
                capital_type=capital_type,
            )
            CapitalService.add_balance(capital, salary.amount)

            salary.is_deleted = True
            salary.save()

            JournalService.log_delete(
                user=deleted_by,
                instance=salary,
                old_data=old_data,
            )

            return salary
