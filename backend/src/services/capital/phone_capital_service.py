"""Phone capital service: owner investment operations."""

from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from src.core.models import PhoneCapital
from src.shared.permissions import get_owner_branch_ids


class PhoneCapitalService:
    """Owner-facing service for PhoneCapital mutations."""

    @staticmethod
    def _validate_owner_branch(owner, branch):
        """Return branch instance after confirming owner access."""
        from src.core.models import Branch

        branch_id = getattr(branch, "id", None)
        if branch_id is None:
            try:
                branch_id = int(branch)
            except (TypeError, ValueError):
                raise ValidationError(_("Noto'g'ri filial."))

        if branch_id not in set(get_owner_branch_ids(owner)):
            raise ValidationError(_("Bu filial sizga tegishli emas."))

        try:
            return Branch.objects.get(pk=branch_id, is_deleted=False)
        except Branch.DoesNotExist:
            raise ValidationError(_("Filial topilmadi."))

    @staticmethod
    def _current_month_start():
        return timezone.localdate().replace(day=1)

    @staticmethod
    @transaction.atomic
    def add_investment(owner, branch, amount):
        """Add investment to current-month PhoneCapital, creating the row if absent.

        Accumulated: multiple calls in the same month increase invested_amount and
        current_balance each time.
        """
        amount = Decimal(str(amount))
        if amount <= 0:
            raise ValidationError(_("Miqdor musbat bo'lishi kerak."))

        branch_obj = PhoneCapitalService._validate_owner_branch(owner, branch)
        month_start = PhoneCapitalService._current_month_start()

        capital = (
            PhoneCapital.objects.select_for_update()
            .filter(branch=branch_obj, month=month_start, is_deleted=False)
            .first()
        )

        if capital:
            capital.invested_amount = Decimal(str(capital.invested_amount)) + amount
            capital.current_balance = Decimal(str(capital.current_balance)) + amount
            capital.save(update_fields=["invested_amount", "current_balance", "updated_at"])
        else:
            capital = PhoneCapital.objects.create(
                branch=branch_obj,
                month=month_start,
                invested_amount=amount,
                current_balance=amount,
            )
        return capital

    @staticmethod
    @transaction.atomic
    def reset_current_month(owner, branch):
        """Reset invested_amount=0 and subtract old invested_amount from current_balance.

        Only the current month is resettable. Past months are not affected.
        """
        branch_obj = PhoneCapitalService._validate_owner_branch(owner, branch)
        month_start = PhoneCapitalService._current_month_start()

        capital = (
            PhoneCapital.objects.select_for_update()
            .filter(branch=branch_obj, month=month_start, is_deleted=False)
            .first()
        )

        if not capital:
            raise ValidationError(_("Joriy oy uchun telefon kapitali topilmadi."))

        old_invested = Decimal(str(capital.invested_amount))
        capital.current_balance = Decimal(str(capital.current_balance)) - old_invested
        capital.invested_amount = Decimal("0.00")
        capital.save(update_fields=["invested_amount", "current_balance", "updated_at"])
        return capital