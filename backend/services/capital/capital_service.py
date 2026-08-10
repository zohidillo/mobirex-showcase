from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils.translation import gettext_lazy as _

from src.core.models import AccessoryCapital, PhoneCapital


def _validate_decimal(value, field_name):
    if not isinstance(value, Decimal):
        raise ValidationError(
            _("%(field)s qiymati Decimal bo‘lishi kerak. Iltimos, avval kapital kiriting.")
            % {"field": field_name}
        )


class CapitalService:
    @staticmethod
    def _get_or_create_capital(model, branch, month_start):
        capital, _ = model.objects.select_for_update().get_or_create(
            branch=branch,
            month=month_start,
            is_deleted=False,
            defaults={
                "invested_amount": Decimal("0"),
                "current_balance": Decimal("0"),
            },
        )
        return capital

    @staticmethod
    def get_phone_capital(branch, month_start):
        return CapitalService._get_or_create_capital(PhoneCapital, branch, month_start)

    @staticmethod
    def get_accessory_capital(branch, month_start):
        return CapitalService._get_or_create_capital(AccessoryCapital, branch, month_start)

    @staticmethod
    def get_capital_for_user(user, branch, month_start, capital_type=None):
        if not branch:
            raise ValidationError(_("Filial tanlash shart."))

        if user.has_role("PHONE_SELLER", branch):
            if capital_type and capital_type != "phone":
                raise ValidationError(_("Ruxsat yo‘q."))
            return CapitalService.get_phone_capital(branch, month_start)

        if user.has_role("ACCESSORY_SELLER", branch):
            if capital_type and capital_type != "accessory":
                raise ValidationError(_("Ruxsat yo‘q."))
            return CapitalService.get_accessory_capital(branch, month_start)

        if (
            user.is_superuser
            or user.is_cashier
            or user.has_role("OWNER", branch)
            or getattr(branch, "owner_id", None) == user.id
        ):
            if not capital_type:
                raise ValidationError(_("Egasi kapital turini ko‘rsatishi shart."))
            if capital_type == "phone":
                return CapitalService.get_phone_capital(branch, month_start)
            if capital_type == "accessory":
                return CapitalService.get_accessory_capital(branch, month_start)
            raise ValidationError(_("Noto‘g‘ri kapital turi."))

        raise ValidationError(_("Ruxsat yo‘q."))

    @staticmethod
    def add_balance(capital, amount):
        with transaction.atomic():
            _validate_decimal(capital.current_balance, "current_balance")
            _validate_decimal(amount, "amount")
            capital.current_balance = capital.current_balance + amount
            capital.save(update_fields=["current_balance", "updated_at"])

    @staticmethod
    def subtract_balance(capital, amount):
        with transaction.atomic():
            _validate_decimal(capital.current_balance, "current_balance")
            _validate_decimal(amount, "amount")
            capital.current_balance = capital.current_balance - amount
            capital.save(update_fields=["current_balance", "updated_at"])

    @staticmethod
    def add_investment(capital, amount):
        with transaction.atomic():
            _validate_decimal(capital.current_balance, "current_balance")
            _validate_decimal(amount, "amount")
            capital.invested_amount = capital.invested_amount + amount
            capital.current_balance = capital.current_balance + amount
            capital.save(update_fields=["invested_amount", "current_balance", "updated_at"])

    @staticmethod
    def subtract_investment(capital, amount):
        with transaction.atomic():
            _validate_decimal(capital.current_balance, "current_balance")
            _validate_decimal(amount, "amount")
            capital.invested_amount = capital.invested_amount - amount
            capital.current_balance = capital.current_balance - amount
            capital.save(update_fields=["invested_amount", "current_balance", "updated_at"])

    @staticmethod
    def add_invested_amount_only(capital, amount):
        """Increase invested_amount without changing current_balance (used for accessory rollover)."""
        with transaction.atomic():
            _validate_decimal(capital.invested_amount, "invested_amount")
            _validate_decimal(amount, "amount")
            capital.invested_amount = capital.invested_amount + amount
            capital.save(update_fields=["invested_amount", "updated_at"])

    @staticmethod
    def adjust_balance_difference(capital, difference):
        with transaction.atomic():
            _validate_decimal(capital.current_balance, "current_balance")
            _validate_decimal(difference, "difference")
            capital.current_balance = capital.current_balance + difference
            capital.save(update_fields=["current_balance", "updated_at"])

    @staticmethod
    def reverse_balance(capital, amount):
        with transaction.atomic():
            _validate_decimal(capital.current_balance, "current_balance")
            _validate_decimal(amount, "amount")
            capital.current_balance = capital.current_balance - amount
            capital.save(update_fields=["current_balance", "updated_at"])
