from decimal import Decimal

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
        raise ValidationError(_("Siz bu qarz yo‘nalishi uchun to‘lov qila olmaysiz."))


class DebtPaymentService:
    @staticmethod
    def pay_debt(debt, amount, paid_by, note):
        with transaction.atomic():
            debt = (
                Debt.objects.select_for_update()
                .select_related("branch", "created_by")
                .get(pk=debt.pk)
            )
            if debt.direction not in {"WE_GAVE", "WE_TOOK"}:
                raise ValidationError(_("Qarz yo‘nalishi noto‘g‘ri."))
            _validate_domain_access(paid_by, debt)
            ensure_debt_is_in_current_month(
                debt,
                message=_("Faqat joriy oy qarziga to‘lov qilish mumkin."),
            )

            month_start = get_debt_month_start(debt)
            capital = _get_capital_for_debt(debt, month_start)

            if debt.direction == "WE_GAVE":
                CapitalService.add_balance(capital, amount)
            else:
                CapitalService.subtract_balance(capital, amount)

            payment = DebtPayment.objects.create(
                debt=debt,
                amount=amount,
                remaining_balance=Decimal("0.00"),
                paid_by=paid_by,
                note=note,
            )
            RecalculateDebtService.recalculate(debt)
            debt.refresh_from_db(fields=["remaining_amount"])
            payment.refresh_from_db()

            JournalService.log_create(
                user=paid_by,
                instance=payment,
                new_data=_snapshot(payment),
            )

            return payment


class DebtPaymentCreateService:
    @staticmethod
    def create_payment(debt, amount, paid_by, note):
        return DebtPaymentService.pay_debt(debt, amount, paid_by, note)


class DebtPaymentUpdateService:
    @staticmethod
    def update_payment(payment, validated_data, updated_by):
        with transaction.atomic():
            old_data = _snapshot(payment)
            old_amount = payment.amount
            new_amount = validated_data.get("amount", old_amount)

            if "debt" in validated_data and validated_data["debt"] != payment.debt:
                raise ValidationError(_("Qarzni o‘zgartirib bo‘lmaydi."))

            debt = Debt.objects.select_for_update().get(pk=payment.debt_id)
            if debt.direction not in {"WE_GAVE", "WE_TOOK"}:
                raise ValidationError(_("Qarz yo‘nalishi noto‘g‘ri."))
            _validate_domain_access(updated_by, debt)
            ensure_debt_is_in_current_month(
                debt,
                message=_("Faqat joriy oy qarzi to‘lovini o‘zgartirish mumkin."),
            )

            difference = new_amount - old_amount
            if difference != 0:
                month_start = get_debt_month_start(debt)
                capital = _get_capital_for_debt(debt, month_start)

                if debt.direction == "WE_GAVE":
                    if difference > 0:
                        CapitalService.add_balance(capital, difference)
                    else:
                        CapitalService.subtract_balance(capital, abs(difference))
                else:
                    if difference > 0:
                        CapitalService.subtract_balance(capital, difference)
                    else:
                        CapitalService.add_balance(capital, abs(difference))

            for attr, value in validated_data.items():
                setattr(payment, attr, value)
            payment.save()
            RecalculateDebtService.recalculate(debt)
            payment.refresh_from_db()

            JournalService.log_update(
                user=updated_by,
                instance=payment,
                old_data=old_data,
                new_data=_snapshot(payment),
            )

            return payment


class DebtPaymentDeleteService:
    @staticmethod
    def delete_payment(payment, deleted_by):
        with transaction.atomic():
            old_data = _snapshot(payment)
            debt = Debt.objects.select_for_update().get(pk=payment.debt_id)
            if debt.direction not in {"WE_GAVE", "WE_TOOK"}:
                raise ValidationError(_("Qarz yo‘nalishi noto‘g‘ri."))
            _validate_domain_access(deleted_by, debt)
            ensure_debt_is_in_current_month(
                debt,
                message=_("Faqat joriy oy qarzi to‘lovini o‘chirish mumkin."),
            )

            month_start = get_debt_month_start(debt)
            capital = _get_capital_for_debt(debt, month_start)

            if debt.direction == "WE_GAVE":
                CapitalService.subtract_balance(capital, payment.amount)
            else:
                CapitalService.add_balance(capital, payment.amount)

            payment.is_deleted = True
            payment.save(update_fields=["is_deleted", "updated_at"])
            RecalculateDebtService.recalculate(debt)

            JournalService.log_delete(
                user=deleted_by,
                instance=payment,
                old_data=old_data,
            )

            return payment
