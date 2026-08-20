from django.core.exceptions import PermissionDenied, ValidationError
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


def _determine_debt_domain(created_by, branch):
    branch_id = getattr(branch, "id", branch)
    if created_by.has_role("PHONE_SELLER", branch_id):
        return Debt.DOMAIN_PHONE
    if created_by.has_role("ACCESSORY_SELLER", branch_id):
        return Debt.DOMAIN_ACCESSORY
    raise PermissionDenied(_("Faqat sotuvchilar qarz yarata oladi."))


class DebtCreateService:
    @staticmethod
    def create_debt(branch, f_name=None, amount=None, direction=None, created_by=None, note=None):
        with transaction.atomic():
            if direction not in {"WE_GAVE", "WE_TOOK"}:
                raise ValidationError(_("Qarz yo’nalishi noto’g’ri."))
            if branch is None:
                raise PermissionDenied(_("Filial topilmadi."))

            month_start = _month_start(timezone.localtime())
            domain = _determine_debt_domain(created_by, branch)
            capital_type = "accessory" if domain == Debt.DOMAIN_ACCESSORY else "phone"
            capital = CapitalService.get_capital_for_user(
                created_by,
                branch,
                month_start,
                capital_type=capital_type,
            )

            if direction == "WE_GAVE":
                CapitalService.subtract_balance(capital, amount)
            else:
                CapitalService.add_balance(capital, amount)

            debt = Debt.objects.create(
                branch=branch,
                created_by=created_by,
                f_name=f_name,
                domain=domain,
                amount=amount,
                remaining_amount=amount,
                direction=direction,
                note=note,
            )

            JournalService.log_create(
                user=created_by,
                instance=debt,
                new_data=_snapshot(debt),
            )

            return debt
