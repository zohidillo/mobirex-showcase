from decimal import Decimal, InvalidOperation

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from src.core.models import Payment, TransactionLog, User as CustomUser
from src.services.journal import JournalService

from .grace_status import GraceStatusService
from .utils import snapshot_instance


class PaymentApplyService:
    @staticmethod
    def create_payment(*, user, amount, payment_type, added_by):
        try:
            amount = amount if isinstance(amount, Decimal) else Decimal(str(amount))
        except (InvalidOperation, TypeError, ValueError):
            raise ValidationError(_("Noto‘g‘ri summa."))
        if amount <= 0:
            raise ValidationError(_("Summa noldan katta bo‘lishi kerak."))

        with transaction.atomic():
            locked_user = CustomUser.objects.select_for_update().get(pk=user.pk, is_deleted=False)
            current_date = timezone.localdate()
            balance_before = locked_user.balance or Decimal("0.00")
            payment = Payment.objects.create(
                user=locked_user,
                amount=amount,
                payment_type=payment_type,
                added_by=added_by,
            )

            user_old_data = snapshot_instance(locked_user)
            locked_user.balance = balance_before + amount
            update_fields = ["balance"]

            if locked_user.is_vip:
                if locked_user.account_status != GraceStatusService.VIP:
                    locked_user.account_status = GraceStatusService.VIP
                    update_fields.append("account_status")
                if locked_user.grace_start_date is not None:
                    locked_user.grace_start_date = None
                    update_fields.append("grace_start_date")
            elif locked_user.balance >= 0:
                if locked_user.account_status != GraceStatusService.ACTIVE:
                    locked_user.account_status = GraceStatusService.ACTIVE
                    update_fields.append("account_status")
                if locked_user.grace_start_date is not None:
                    locked_user.grace_start_date = None
                    update_fields.append("grace_start_date")
            else:
                if locked_user.grace_start_date is None:
                    locked_user.grace_start_date = current_date
                    update_fields.append("grace_start_date")
                desired_status = GraceStatusService.resolve_status(
                    locked_user,
                    current_date=current_date,
                )
                if locked_user.account_status != desired_status:
                    locked_user.account_status = desired_status
                    update_fields.append("account_status")

            locked_user.save(update_fields=list(dict.fromkeys(update_fields + ["updated_at"])))

            transaction_log = TransactionLog.objects.create(
                user=locked_user,
                type="payment",
                amount=amount,
                charge_date=payment.added_at or timezone.now(),
                balance_before=balance_before,
                balance_after=locked_user.balance,
            )

            JournalService.log_create(
                user=added_by,
                instance=payment,
                new_data=snapshot_instance(payment),
            )
            JournalService.log_update(
                user=added_by,
                instance=locked_user,
                old_data=user_old_data,
                new_data=snapshot_instance(locked_user),
            )
            JournalService.log_create(
                user=added_by,
                instance=transaction_log,
                new_data=snapshot_instance(transaction_log),
            )

            return payment
