import logging
from decimal import Decimal

from django.db.models import DecimalField, ExpressionWrapper, F, Sum
from django.utils import timezone

from src.core.models import Accessory, AccessoryCapital


logger = logging.getLogger(__name__)

ZERO_DECIMAL = Decimal("0.00")


def _month_start(value):
    if hasattr(value, "date"):
        value = value.date()
    return value.replace(day=1)


def calculate_inventory_value(branch):
    inventory_value_expr = ExpressionWrapper(
        F("stock") * F("unit_cost"),
        output_field=DecimalField(max_digits=18, decimal_places=2),
    )
    totals = Accessory.all_objects.filter(
        branch=branch,
        is_deleted=False,
        is_active=True,
        stock__gt=0,
    ).aggregate(
        inventory_value=Sum(inventory_value_expr),
    )
    inventory_value = totals.get("inventory_value") or ZERO_DECIMAL
    logger.debug(
        "Accessory inventory value calculated",
        extra={
            "branch_id": getattr(branch, "id", branch),
            "inventory_value": str(inventory_value),
        },
    )
    return inventory_value


class AccessoryAnalyticsService:
    @staticmethod
    def get_inventory_value(branch):
        return calculate_inventory_value(branch)

    @staticmethod
    def get_current_balance(branch):
        month_start = _month_start(timezone.localtime())
        current_balance = (
            AccessoryCapital.objects.filter(
                branch=branch,
                month=month_start,
            )
            .values_list("current_balance", flat=True)
            .first()
        )
        return current_balance or ZERO_DECIMAL

    @staticmethod
    def get_total_capital(branch):
        inventory_value = AccessoryAnalyticsService.get_inventory_value(branch)
        current_balance = AccessoryAnalyticsService.get_current_balance(branch)
        total_capital = current_balance + inventory_value

        logger.debug(
            "Accessory total capital calculated",
            extra={
                "branch_id": getattr(branch, "id", branch),
                "inventory_value": str(inventory_value),
                "current_balance": str(current_balance),
                "total_capital": str(total_capital),
            },
        )
        return total_capital


__all__ = [
    "AccessoryAnalyticsService",
    "calculate_inventory_value",
]
