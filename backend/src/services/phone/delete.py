from django.db import transaction
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from src.services.capital import CapitalService
from src.services.journal import JournalService
from src.shared.json_utils import json_safe


def _month_start(value):
    if hasattr(value, "date"):
        value = value.date()
    return value.replace(day=1)


def _snapshot_phone(phone):
    data = {}
    for field in phone._meta.fields:
        value = getattr(phone, field.attname)
        data[field.attname] = json_safe(value)
    return data


class PhoneDeleteService:
    @staticmethod
    def delete_phone(phone, deleted_by):
        if phone.is_month_closed:
            raise ValueError(_("Yopilgan oy telefoni o'chirib bo'lmaydi."))
        with transaction.atomic():
            if phone.is_sold:
                raise ValueError(
                    _("Sotilgan telefonni o‘chirib bo‘lmaydi. Avval qaytarish qiling.")
                )

            now = timezone.localtime()
            phone_added_at = timezone.localtime(phone.added_at)
            if phone_added_at.year != now.year or phone_added_at.month != now.month:
                raise ValueError(_("Telefon faqat qo‘shilgan oyda o‘chirilishi mumkin."))

            old_data = _snapshot_phone(phone)
            month_start = _month_start(now)
            capital = CapitalService.get_capital_for_user(
                deleted_by,
                phone.branch,
                month_start,
                capital_type="phone",
            )

            CapitalService.add_balance(capital, phone.cost_price)

            phone.is_deleted = True
            phone.save()

            JournalService.log_delete(
                user=deleted_by,
                instance=phone,
                old_data=old_data,
            )

            return phone
