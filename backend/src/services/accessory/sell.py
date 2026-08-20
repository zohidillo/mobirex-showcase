from django.db import transaction
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from src.core.models import Accessory, AccessorySale
from src.services.capital import CapitalService
from src.services.journal import JournalService
from src.shared.json_utils import json_safe


def _month_start(value):
    if hasattr(value, "date"):
        value = value.date()
    return value.replace(day=1)


def _snapshot_sale(sale):
    data = {}
    for field in sale._meta.fields:
        value = getattr(sale, field.attname)
        data[field.attname] = json_safe(value)
    return data


class AccessorySellService:
    @staticmethod
    def sell_accessory(accessory, quantity, total_price, sold_by):
        with transaction.atomic():
            accessory = Accessory.objects.select_for_update().get(pk=accessory.pk)

            if accessory.is_month_closed:
                raise ValueError(_("Yopilgan oy aksessuari sotib bo'lmaydi."))

            if accessory.stock < quantity:
                raise ValueError(_("Aksessuar zaxirasi yetarli emas."))

            total_cost = accessory.unit_cost * quantity
            profit = total_price - total_cost
            sold_at = timezone.now()

            sale = AccessorySale.objects.create(
                accessory=accessory,
                branch=accessory.branch,
                quantity=quantity,
                unit_cost=accessory.unit_cost,
                total_cost=total_cost,
                total_price=total_price,
                profit=profit,
                sold_by=sold_by,
                sold_at=sold_at,
            )

            accessory.stock = accessory.stock - quantity
            accessory.save()

            month_start = _month_start(sold_at)
            capital = CapitalService.get_capital_for_user(
                sold_by,
                accessory.branch,
                month_start,
                capital_type="accessory",
            )
            sell_price = sale.total_price
            CapitalService.add_balance(capital, sell_price)

            JournalService.log_create(
                user=sold_by,
                instance=sale,
                new_data=_snapshot_sale(sale),
            )

            return sale
