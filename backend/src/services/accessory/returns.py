from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from src.services.capital import CapitalService
from src.services.journal import JournalService
from src.shared.json_utils import json_safe


def _snapshot(instance):
    data = {}
    for field in instance._meta.fields:
        value = getattr(instance, field.attname)
        data[field.attname] = json_safe(value)
    return data


class AccessoryReturnService:
    @staticmethod
    def return_sale(sale, *, returned_by):
        if not (
            returned_by.has_role("ACCESSORY_SELLER", sale.branch)
            or returned_by.has_role("OWNER", sale.branch)
        ):
            raise PermissionDenied(_("Sizga bu amalni bajarish mumkin emas."))

        if sale.accessory.is_deleted:
            raise ValidationError(_("O'chirilgan aksessuar uchun qaytarish mumkin emas."))

        now = timezone.localtime()
        sold_at = timezone.localtime(sale.sold_at)
        if sold_at.year != now.year or sold_at.month != now.month:
            raise ValidationError(_("Oldingi oy sotuvlarini qaytarib bo‘lmaydi."))

        with transaction.atomic():
            old_data = _snapshot(sale)
            accessory = sale.accessory

            accessory.stock = accessory.stock + sale.quantity
            accessory.save()

            month_start = sold_at.date().replace(day=1)
            capital = CapitalService.get_capital_for_user(
                returned_by,
                accessory.branch,
                month_start,
                capital_type="accessory",
            )
            CapitalService.subtract_balance(capital, sale.total_price)

            sale.is_deleted = True
            sale.save()

            JournalService.log_update(
                user=returned_by,
                instance=sale,
                old_data=old_data,
                new_data=_snapshot(sale),
            )

        return sale

