from decimal import Decimal, InvalidOperation

from django.core.exceptions import PermissionDenied, ValidationError
from django.utils.translation import gettext_lazy as _

from src.shared.permissions import can_access_branch


def _to_decimal(value):
    """Convert a raw value into Decimal."""
    if value is None:
        raise ValidationError(_("Summani kiritish shart."))

    try:
        return value if isinstance(value, Decimal) else Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise ValidationError(_("Noto‘g‘ri summa.")) from exc


def validate_positive_amount(amount):
    """Validate that the given amount is positive."""
    normalized_amount = _to_decimal(amount)
    if normalized_amount <= 0:
        raise ValidationError(_("Summa noldan katta bo‘lishi kerak."))
    return normalized_amount


def check_stock_available(product, quantity):
    """Validate that enough stock exists for the quantity."""
    if product is None:
        raise ValidationError(_("Mahsulot topilmadi."))

    normalized_quantity = validate_positive_amount(quantity)
    available_stock = Decimal(str(getattr(product, "stock", 0) or 0))
    if available_stock < normalized_quantity:
        raise ValidationError(_("Aksessuar zaxirasi yetarli emas."))
    return normalized_quantity


def validate_debt_payment(debt, amount):
    """Validate that a debt payment does not exceed the balance."""
    if debt is None:
        raise ValidationError(_("Qarz topilmadi."))

    normalized_amount = validate_positive_amount(amount)
    remaining_amount = Decimal(str(getattr(debt, "remaining_amount", 0) or 0))
    if normalized_amount > remaining_amount:
        raise ValidationError(_("Summa qarz qoldig‘idan oshib ketdi."))
    return normalized_amount


def validate_branch_access(user, branch):
    """Validate that the user can access the branch."""
    if not can_access_branch(user, branch):
        raise PermissionDenied(_("Sizda bu filialga ruxsat yo‘q."))
    return branch
