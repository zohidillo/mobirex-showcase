from dataclasses import dataclass
from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from src.core.models import TransactionLog, User as CustomUser

from .grace_status import GraceStatusService


@dataclass
class DailyChargeResult:
    user_id: int
    status: str
    charged: bool = False
    skipped_reason: str = ""
    error: str = ""
    log_id: int | None = None
    balance_before: Decimal = Decimal("0.00")
    balance_after: Decimal = Decimal("0.00")


class DailyChargeService:
    @classmethod
    def iter_charge_results(cls, *, charge_at=None, chunk_size=500):
        queryset = (
            CustomUser.objects.filter(is_deleted=False)
            .order_by("id")
            .values_list("id", flat=True)
        )
        for user_id in queryset.iterator(chunk_size=chunk_size):
            try:
                yield cls.charge_user_by_id(user_id, charge_at=charge_at)
            except Exception as exc:  # pragma: no cover - defensive batch safety
                yield DailyChargeResult(
                    user_id=user_id,
                    status="error",
                    skipped_reason="error",
                    error=str(exc),
                )

    @classmethod
    def charge_user(cls, user, charge_at=None):
        user_id = getattr(user, "pk", user)
        return cls.charge_user_by_id(user_id, charge_at=charge_at)

    @classmethod
    def charge_user_by_id(cls, user_id, charge_at=None):
        charge_at = charge_at or timezone.now()
        charge_day = timezone.localdate(charge_at)

        with transaction.atomic():
            user = CustomUser.objects.select_for_update().get(pk=user_id, is_deleted=False)
            status = GraceStatusService.sync_user_status(user, current_date=charge_day, persist=True)

            if status == GraceStatusService.VIP:
                return DailyChargeResult(
                    user_id=user.id,
                    status=status,
                    skipped_reason="vip",
                )

            if status == GraceStatusService.BLOCKED:
                return DailyChargeResult(
                    user_id=user.id,
                    status=status,
                    skipped_reason="blocked",
                )

            existing_log = (
                TransactionLog.all_objects.filter(
                    user=user,
                    type="daily_charge",
                    charge_day=charge_day,
                    is_deleted=False,
                )
                .only("id")
                .first()
            )
            if existing_log:
                return DailyChargeResult(
                    user_id=user.id,
                    status=status,
                    skipped_reason="duplicate",
                    log_id=existing_log.id,
                )

            balance_before = user.balance or Decimal("0.00")
            fee = user.daily_fee or Decimal("0.00")
            user.balance = balance_before - fee
            update_fields = ["balance"]

            if user.balance < 0:
                if user.grace_start_date is None:
                    user.grace_start_date = charge_day
                    update_fields.append("grace_start_date")
                if user.account_status != GraceStatusService.GRACE:
                    user.account_status = GraceStatusService.GRACE
                    update_fields.append("account_status")
            else:
                if user.grace_start_date is not None:
                    user.grace_start_date = None
                    update_fields.append("grace_start_date")
                if user.account_status != GraceStatusService.ACTIVE:
                    user.account_status = GraceStatusService.ACTIVE
                    update_fields.append("account_status")

            user.save(update_fields=list(dict.fromkeys(update_fields + ["updated_at"])))

            daily_log = TransactionLog.objects.create(
                user=user,
                type="daily_charge",
                amount=fee,
                charge_date=charge_at,
                balance_before=balance_before,
                balance_after=user.balance,
            )

            return DailyChargeResult(
                user_id=user.id,
                status=user.account_status,
                charged=True,
                log_id=daily_log.id,
                balance_before=balance_before,
                balance_after=user.balance,
            )
