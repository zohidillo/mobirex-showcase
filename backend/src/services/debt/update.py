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
        raise ValidationError(_("Siz bu qarz yo‘nalishini o‘zgartira olmaysiz."))


class DebtUpdateService:
    @staticmethod
    def update_debt(debt, validated_data, updated_by):
        with transaction.atomic():
            if debt.direction not in {"WE_GAVE", "WE_TOOK"}:
                raise ValidationError(_("Qarz yo‘nalishi noto‘g‘ri."))
            _validate_domain_access(updated_by, debt)
            ensure_debt_is_in_current_month(
                debt,
                message=_("Faqat joriy oy qarzini o‘zgartirish mumkin."),
            )
            if "domain" in validated_data and validated_data["domain"] != debt.domain:
                raise ValidationError(_("Qarz yo‘nalishini o‘zgartirib bo‘lmaydi."))

            old_data = _snapshot(debt)
            old_amount = debt.amount
            new_amount = validated_data.get("amount", old_amount)

            if new_amount != old_amount:
                difference = new_amount - old_amount
                month_start = get_debt_month_start(debt)
                capital = _get_capital_for_debt(debt, month_start)

                if debt.direction == "WE_GAVE":
                    if difference > 0:
                        CapitalService.subtract_balance(capital, difference)
                    elif difference < 0:
                        CapitalService.add_balance(capital, abs(difference))
                else:
                    if difference > 0:
                        CapitalService.add_balance(capital, difference)
                    elif difference < 0:
                        CapitalService.subtract_balance(capital, abs(difference))

            for attr, value in validated_data.items():
                setattr(debt, attr, value)
            debt.save()
            RecalculateDebtService.recalculate(debt)
            debt.refresh_from_db()

            JournalService.log_update(
                user=updated_by,
                instance=debt,
                old_data=old_data,
                new_data=_snapshot(debt),
            )

            return debt
