from decimal import Decimal

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from src.services.capital import CapitalService
from src.services.journal import JournalService
from src.services.phone.delete import PhoneDeleteService
from src.services.phone.sell import PhoneSellService
from src.shared.json_utils import json_safe


def _snapshot_phone(phone):
    data = {}
    for field in phone._meta.fields:
        value = getattr(phone, field.attname)
        data[field.attname] = json_safe(value)
    return data


class PhoneService:
    """High-level phone operations with shared validations."""

    @staticmethod
    def sell_phone(phone, *, sell_price, sold_by):
        """Sell a phone when the acting user has branch access and the phone is unsold."""
        if not phone or getattr(phone, "is_deleted", False):
            raise ValidationError(_("Telefon topilmadi."))

        if phone.is_sold:
            raise ValidationError(_("Telefon allaqachon sotilgan."))

        if not (
            sold_by.has_role("PHONE_SELLER", phone.branch)
            or sold_by.has_role("OWNER", phone.branch)
        ):
            raise PermissionDenied(_("Sizga bu amalni bajarish mumkin emas."))

        return PhoneSellService.sell_phone(phone, sell_price=sell_price, sold_by=sold_by)

    @staticmethod
    def return_phone(phone, *, returned_by):
        """Return a sold phone. Only current-month sales may be returned."""
        if not phone or getattr(phone, "is_deleted", False):
            raise ValidationError(_("Telefon topilmadi."))

        if not phone.is_sold:
            raise ValidationError(_("Telefon sotilmagan."))

        if not (
            returned_by.has_role("PHONE_SELLER", phone.branch)
            or returned_by.has_role("OWNER", phone.branch)
        ):
            raise PermissionDenied(_("Sizga bu amalni bajarish mumkin emas."))

        if not phone.sold_at:
            raise ValidationError(_("Sizga bu amalni bajarish mumkin emas."))

        now = timezone.localtime()
        sold_at = timezone.localtime(phone.sold_at)
        if sold_at.year != now.year or sold_at.month != now.month:
            raise ValidationError(_("Oldingi oy sotuvlarini qaytarib bo‘lmaydi."))

        with transaction.atomic():
            old_data = _snapshot_phone(phone)
            sell_price = phone.sell_price or Decimal("0")
            month_start = sold_at.date().replace(day=1)
            capital = CapitalService.get_capital_for_user(
                returned_by,
                phone.branch,
                month_start,
                capital_type="phone",
            )
            CapitalService.subtract_balance(capital, sell_price)

            phone.is_sold = False
            phone.sold_at = None
            phone.sold_by = None
            phone.sell_price = None
            phone.save()

            JournalService.log_update(
                user=returned_by,
                instance=phone,
                old_data=old_data,
                new_data=_snapshot_phone(phone),
            )

        return phone

    @staticmethod
    def delete_phone(phone, *, deleted_by):
        """Delete a phone when deletion rules and branch isolation allow it."""
        if not phone or getattr(phone, "is_deleted", False):
            raise ValidationError(_("Telefon topilmadi."))

        user = deleted_by
        if user.has_role("PHONE_SELLER", phone.branch):
            if phone.added_by_id != user.id:
                raise PermissionDenied(_("Sizga bu amalni bajarish mumkin emas."))
        elif user.has_role("OWNER", phone.branch):
            pass
        else:
            raise PermissionDenied(_("Sizga bu amalni bajarish mumkin emas."))

        try:
            return PhoneDeleteService.delete_phone(phone, deleted_by=user)
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc

