from django.db import transaction
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from src.core.models import AccessorySale
from src.services.capital import CapitalService
from src.services.journal import JournalService
from src.shared.json_utils import json_safe


def _month_start(value):
    if hasattr(value, "date"):
        value = value.date()
    return value.replace(day=1)


def _snapshot_accessory(accessory):
    data = {}
    for field in accessory._meta.fields:
        value = getattr(accessory, field.attname)
        data[field.attname] = json_safe(value)
    return data


class AccessoryDeleteService:
    @staticmethod
    def delete_accessory(accessory, deleted_by):
        if accessory.is_month_closed:
            raise ValueError(_("Yopilgan oy aksessuari o'chirib bo'lmaydi."))
        with transaction.atomic():
            now = timezone.localtime()
            accessory_added_at = timezone.localtime(accessory.added_at)
            if accessory_added_at.year != now.year or accessory_added_at.month != now.month:
                raise ValueError(_("Aksessuar faqat qo‘shilgan oyda o‘chirilishi mumkin."))

            active_sales_count = AccessorySale.objects.filter(
                accessory=accessory, is_deleted=False
            ).count()
            if active_sales_count > 0:
                raise ValueError(
                    _("Aksessuar o'chirib bo'lmaydi: %(count)d ta aktiv sotuv mavjud. Avval ularni qaytaring.")
                    % {"count": active_sales_count}
                )

            old_data = _snapshot_accessory(accessory)
            remaining_value = accessory.stock * accessory.unit_cost

            month_start = _month_start(now)
            capital = CapitalService.get_capital_for_user(
                deleted_by,
                accessory.branch,
                month_start,
                capital_type="accessory",
            )
            capital.invested_amount = capital.invested_amount - remaining_value
            capital.save()

            accessory.is_deleted = True
            accessory.save()

            JournalService.log_delete(
                user=deleted_by,
                instance=accessory,
                old_data=old_data,
            )

            return accessory
