from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from src.core.models import *
from src.services.capital import CapitalService
from src.services.journal import JournalService
from src.shared.json_utils import json_safe
from src.shared.permissions import get_seller_domain_for_branch, user_can_access_owner_branch


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


def _is_current_month(dt):
    now = timezone.localtime()
    local_dt = timezone.localtime(dt)
    return local_dt.year == now.year and local_dt.month == now.month


class ExpenseDeleteService:
    @staticmethod
    def _validate_deleter(expense, deleted_by):
        if not _is_current_month(expense.added_at):
            raise ValidationError(_("Xarajatni faqat joriy oyda o'chirish mumkin."))

        if user_can_access_owner_branch(deleted_by, expense.branch):
            return

        if expense.created_by_id != getattr(deleted_by, "id", None):
            raise ValidationError(_("Sizga bu amalni bajarish mumkin emas."))
        if not get_seller_domain_for_branch(deleted_by, expense.branch):
            raise ValidationError(_("Faqat sotuvchilar xarajat o'chira oladi."))

    @staticmethod
    def _get_capital_type(expense):
        if expense.capital_type in {
            Expense.CAPITAL_TYPE_PHONE,
            Expense.CAPITAL_TYPE_ACCESSORY,
        }:
            return expense.capital_type

        seller_domain = get_seller_domain_for_branch(expense.created_by, expense.branch)
        if seller_domain == "PHONE":
            return Expense.CAPITAL_TYPE_PHONE
        if seller_domain == "ACCESSORY":
            return Expense.CAPITAL_TYPE_ACCESSORY

        if expense.type == "SHOP_EXPENSE":
            return Expense.CAPITAL_TYPE_PHONE
        if expense.type == "EMPLOYEE_EXPENSE":
            return Expense.CAPITAL_TYPE_ACCESSORY

        raise ValidationError(_("Xarajat uchun kapital turi aniqlanmadi."))

    @staticmethod
    def delete_expense(expense, deleted_by):
        with transaction.atomic():
            ExpenseDeleteService._validate_deleter(expense, deleted_by)
            old_data = _snapshot(expense)
            month_start = _month_start(expense.added_at)
            capital_type = ExpenseDeleteService._get_capital_type(expense)
            if capital_type == Expense.CAPITAL_TYPE_PHONE:
                capital = CapitalService.get_phone_capital(expense.branch, month_start)
            else:
                capital = CapitalService.get_accessory_capital(expense.branch, month_start)
            CapitalService.add_balance(capital, expense.amount)

            expense.is_deleted = True
            expense.save(update_fields=["is_deleted", "updated_at"])

            JournalService.log_delete(
                user=deleted_by,
                instance=expense,
                old_data=old_data,
            )

            return expense
