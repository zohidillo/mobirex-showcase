from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils.translation import gettext_lazy as _

from src.core.models import *
from src.services.capital import CapitalService
from src.services.journal import JournalService
from src.shared.json_utils import json_safe
from src.shared.permissions import user_matches_debt_domain
from .recalculate import RecalculateDebtService
from .snapshot import ensure_debt_is_in_current_month, get_debt_month_start


def _snapshot(instance):
    data = {}
    for field in instance._meta.fields:
        value = getattr(instance, field.attname)
        data[field.attname] = json_safe(value)
    return data


def _resolve_debt_capital_type(debt):
    if debt.domain == Debt.DOMAIN_ACCESSORY:
        return "accessory"
    if debt.domain == Debt.DOMAIN_PHONE:
        return "phone"
    creator = getattr(debt, "created_by", None)
    if creator and creator.has_role("ACCESSORY_SELLER", debt.branch):
        return "accessory"
    if creator and creator.has_role("PHONE_SELLER", debt.branch):
        return "phone"
    return "phone"


def _get_capital_for_debt(debt, month_start):
    capital_type = _resolve_debt_capital_type(debt)
    if capital_type == "accessory":
        return CapitalService.get_accessory_capital(debt.branch, month_start)
    return CapitalService.get_phone_capital(debt.branch, month_start)


def _validate_domain_access(user, debt):
    if not user_matches_debt_domain(user, debt):
        raise ValidationError(_("Siz bu qarz yo‘nalishini o‘chira olmaysiz."))


class DebtDeleteService:
    @staticmethod
    def delete_debt(debt, deleted_by):
        with transaction.atomic():
            debt = (
                Debt.objects.select_for_update()
                .select_related("branch", "created_by")
                .get(pk=debt.pk)
            )
            debt = RecalculateDebtService.recalculate(debt)
            if debt.direction not in {"WE_GAVE", "WE_TOOK"}:
                raise ValidationError(_("Qarz yo‘nalishi noto‘g‘ri."))
            _validate_domain_access(deleted_by, debt)
            ensure_debt_is_in_current_month(
                debt,
                message=_("Faqat joriy oy qarzini o‘chirish mumkin."),
            )

            old_data = _snapshot(debt)
            active_payments = list(
                DebtPayment.objects.select_for_update()
                .filter(debt=debt, is_deleted=False)
                .select_related("paid_by")
            )
            month_start = get_debt_month_start(debt)
            capital = _get_capital_for_debt(debt, month_start)

            if debt.direction == "WE_GAVE":
                CapitalService.add_balance(capital, debt.remaining_amount)
            else:
                CapitalService.subtract_balance(capital, debt.remaining_amount)

            for payment in active_payments:
                payment_old_data = _snapshot(payment)
                payment.is_deleted = True
                payment.save()

                JournalService.log_delete(
                    user=deleted_by,
                    instance=payment,
                    old_data=payment_old_data,
                )

            debt.is_deleted = True
            debt.save()

            JournalService.log_delete(
                user=deleted_by,
                instance=debt,
                old_data=old_data,
            )

            return debt
