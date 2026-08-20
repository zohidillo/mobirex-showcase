import logging
from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from pathlib import Path

from django.conf import settings
from django.core.management import call_command
from django.db import IntegrityError, transaction
from django.utils import timezone

from src.core.models import Accessory, Branch, DashboardSnapshot, MonthClosingRecord, Phone
from src.services.capital import CapitalService
from src.services.dashboard import DashboardService


logger = logging.getLogger("month_closing")

DEFAULT_BATCH_SIZE = 500
BRANCH_ITERATOR_CHUNK_SIZE = 50
STARTED_RECORD_STALE_AFTER = timedelta(hours=6)


@dataclass
class BranchMonthClosingResult:
    branch_id: int
    branch_name: str
    month: date
    dry_run: bool
    skipped: bool = False
    phones_closed: int = 0
    phones_recreated: int = 0
    phone_rollover_amount: Decimal = field(default_factory=lambda: Decimal("0"))
    accessories_processed: int = 0
    accessories_recreated: int = 0
    accessory_rollover_amount: Decimal = field(default_factory=lambda: Decimal("0"))
    phone_inventory_value: Decimal = field(default_factory=lambda: Decimal("0"))
    accessory_inventory_value: Decimal = field(default_factory=lambda: Decimal("0"))
    snapshot_action: str = "none"
    dashboard_data: dict | None = None
    phone_data: dict | None = None
    accessory_data: dict | None = None
    debt_data: dict | None = None
    expense_data: dict | None = None
    salary_data: dict | None = None
    capital_data: dict | None = None
    error: str | None = None


class MonthClosingService:
    @staticmethod
    def _normalize_month(month):
        if month is None:
            raise ValueError("month is required")

        if isinstance(month, str):
            normalized = month.strip()
            for fmt in ("%Y-%m", "%Y-%m-%d"):
                try:
                    month = datetime.strptime(normalized, fmt).date()
                    break
                except ValueError:
                    continue
            else:
                raise ValueError("month must be in YYYY-MM format")
        elif isinstance(month, datetime):
            month = timezone.localdate(month) if timezone.is_aware(month) else month.date()
        elif hasattr(month, "date") and not isinstance(month, date):
            month = month.date()

        if not isinstance(month, date):
            raise ValueError("month must be a date, datetime, or YYYY-MM string")

        return month.replace(day=1)

    @staticmethod
    def resolve_period(reference_time=None, month=None):
        if month is not None:
            closing_month = MonthClosingService._normalize_month(month)
        else:
            current_time = reference_time or timezone.now()
            if timezone.is_naive(current_time):
                current_time = timezone.make_aware(
                    current_time,
                    timezone.get_current_timezone(),
                )
            current_time = timezone.localtime(current_time)
            next_month_start = current_time.date().replace(day=1)
            previous_month_end = next_month_start - timedelta(days=1)
            closing_month = previous_month_end.replace(day=1)

        if closing_month.month == 12:
            next_month_start = date(closing_month.year + 1, 1, 1)
        else:
            next_month_start = date(closing_month.year, closing_month.month + 1, 1)
        previous_month_end = next_month_start - timedelta(days=1)

        previous_month_end_dt = timezone.make_aware(
            datetime.combine(previous_month_end, time(23, 59, 59)),
            timezone.get_current_timezone(),
        )
        next_month_start_dt = timezone.make_aware(
            datetime.combine(next_month_start, time.min),
            timezone.get_current_timezone(),
        )

        return {
            "closing_month": closing_month,
            "next_month_start": next_month_start,
            "previous_month_end_dt": previous_month_end_dt,
            "next_month_start_dt": next_month_start_dt,
        }

    @staticmethod
    def close_all_branches(
        *,
        dry_run=False,
        reference_time=None,
        batch_size=DEFAULT_BATCH_SIZE,
        month=None,
    ):
        period = MonthClosingService.resolve_period(reference_time=reference_time, month=month)
        branches = Branch.objects.filter(is_deleted=False).order_by("id")
        last_id = 0

        while True:
            batch = list(
                branches.select_related("owner").filter(id__gt=last_id)[:BRANCH_ITERATOR_CHUNK_SIZE]
            )
            if not batch:
                break

            for branch in batch:
                last_id = branch.id
                try:
                    result = MonthClosingService.close_branch(
                        branch=branch,
                        closing_month=period["closing_month"],
                        dry_run=dry_run,
                        batch_size=batch_size,
                    )
                except Exception as exc:
                    logger.exception(
                        "Filial #%s uchun %s oyi yopishida xatolik yuz berdi",
                        branch.id,
                        period["closing_month"],
                    )
                    result = BranchMonthClosingResult(
                        branch_id=branch.id,
                        branch_name=branch.name,
                        month=period["closing_month"],
                        dry_run=dry_run,
                        error=str(exc),
                    )
                yield result

    @staticmethod
    def close_branch(
        *,
        branch,
        closing_month,
        next_month_start=None,
        previous_month_end_dt=None,
        next_month_start_dt=None,
        dry_run=False,
        batch_size=DEFAULT_BATCH_SIZE,
    ):
        del previous_month_end_dt, next_month_start_dt, batch_size

        closing_month = MonthClosingService._normalize_month(closing_month)

        if next_month_start is None:
            if closing_month.month == 12:
                next_month_start = date(closing_month.year + 1, 1, 1)
            else:
                next_month_start = date(closing_month.year, closing_month.month + 1, 1)

        result = BranchMonthClosingResult(
            branch_id=branch.id,
            branch_name=branch.name,
            month=closing_month,
            dry_run=dry_run,
        )

        if dry_run:
            with transaction.atomic():
                locked_branch = MonthClosingService._lock_branch(branch)
                record = MonthClosingService._get_closing_record(
                    branch=locked_branch,
                    closing_month=closing_month,
                )
                snapshot = MonthClosingService._get_dashboard_snapshot(
                    branch=locked_branch,
                    closing_month=closing_month,
                )
                payload = MonthClosingService._calculate_snapshot_payload(
                    branch=locked_branch,
                    closing_month=closing_month,
                )
                result.snapshot_action = MonthClosingService._get_dry_run_snapshot_action(
                    record=record,
                    snapshot=snapshot,
                )
                MonthClosingService._populate_result_from_payload(result=result, payload=payload)

                now = timezone.now()
                phones_recreated, phone_rollover_amount = MonthClosingService._rollover_phones(
                    branch=locked_branch,
                    closing_month=closing_month,
                    next_month_start=next_month_start,
                    now=now,
                )
                accessories_recreated, accessory_rollover_amount = MonthClosingService._rollover_accessories(
                    branch=locked_branch,
                    closing_month=closing_month,
                    next_month_start=next_month_start,
                    now=now,
                )
                result.phones_recreated = phones_recreated
                result.phone_rollover_amount = phone_rollover_amount
                result.accessories_recreated = accessories_recreated
                result.accessory_rollover_amount = accessory_rollover_amount

                transaction.set_rollback(True)
                logger.info(
                    "Dry-run: filial #%s uchun %s oyi yopilishi hisoblab chiqildi",
                    locked_branch.id,
                    closing_month,
                )
            return result

        closing_record = MonthClosingService._prepare_closing_record(
            branch=branch,
            closing_month=closing_month,
        )
        if closing_record is None:
            result.skipped = True
            result.snapshot_action = "skipped"
            MonthClosingService._log_skip(
                branch=branch,
                closing_month=closing_month,
                record=MonthClosingRecord.objects.filter(
                    branch=branch,
                    month=closing_month,
                ).first(),
            )
            return result

        try:
            with transaction.atomic():
                locked_branch = MonthClosingService._lock_branch(branch)
                payload = MonthClosingService._calculate_snapshot_payload(
                    branch=locked_branch,
                    closing_month=closing_month,
                )
                snapshot, created = MonthClosingService._persist_dashboard_snapshot(
                    branch=locked_branch,
                    closing_month=closing_month,
                    payload=payload,
                )
                MonthClosingService._populate_result_from_payload(result=result, payload=payload)
                result.snapshot_action = "created" if created else "updated"

                now = timezone.now()
                phones_recreated, phone_rollover_amount = MonthClosingService._rollover_phones(
                    branch=locked_branch,
                    closing_month=closing_month,
                    next_month_start=next_month_start,
                    now=now,
                )
                accessories_recreated, accessory_rollover_amount = MonthClosingService._rollover_accessories(
                    branch=locked_branch,
                    closing_month=closing_month,
                    next_month_start=next_month_start,
                    now=now,
                )
                result.phones_recreated = phones_recreated
                result.phone_rollover_amount = phone_rollover_amount
                result.accessories_recreated = accessories_recreated
                result.accessory_rollover_amount = accessory_rollover_amount

                MonthClosingService._mark_closing_record_completed(
                    record_id=closing_record.pk,
                    result=result,
                )
                logger.info(
                    "Filial #%s uchun %s oyi yopildi (%s): %d telefon, %d aksessuar ko'chirildi",
                    locked_branch.id,
                    closing_month,
                    "created" if created else "updated",
                    phones_recreated,
                    accessories_recreated,
                )
        except Exception:
            MonthClosingService._mark_closing_record_failed(record_id=closing_record.pk)
            raise

        return result

    @staticmethod
    def _rollover_phones(*, branch, closing_month, next_month_start, now):
        month_start_dt = timezone.make_aware(
            datetime.combine(closing_month, time.min),
            timezone.get_current_timezone(),
        )
        next_month_start_dt = timezone.make_aware(
            datetime.combine(next_month_start, time.min),
            timezone.get_current_timezone(),
        )

        unsold_phones = list(
            Phone.objects.select_for_update()
            .filter(
                branch=branch,
                is_deleted=False,
                is_sold=False,
                is_month_closed=False,
                added_at__gte=month_start_dt,
                added_at__lt=next_month_start_dt,
            )
            .order_by("id")
        )

        phones_recreated = 0
        phone_rollover_amount = Decimal("0")

        for phone in unsold_phones:
            already_rolled = Phone.objects.filter(
                rolled_over_from=phone,
                is_deleted=False,
            ).exists()

            phone.is_month_closed = True
            phone.month_closed_at = now
            phone.save(update_fields=["is_month_closed", "month_closed_at", "updated_at"])

            if not already_rolled:
                Phone.objects.create(
                    name=phone.name,
                    category_id=phone.category_id,
                    branch_id=phone.branch_id,
                    imei=phone.imei,
                    storage=phone.storage,
                    color=phone.color,
                    from_by=phone.from_by,
                    cost_price=phone.cost_price,
                    added_by_id=phone.added_by_id,
                    rolled_over_from=phone,
                )
                phones_recreated += 1
                phone_rollover_amount += phone.cost_price

        if phone_rollover_amount > 0:
            capital = CapitalService.get_phone_capital(branch, next_month_start)
            CapitalService.subtract_balance(capital, phone_rollover_amount)

        return phones_recreated, phone_rollover_amount

    @staticmethod
    def _rollover_accessories(*, branch, closing_month, next_month_start, now):
        month_start_dt = timezone.make_aware(
            datetime.combine(closing_month, time.min),
            timezone.get_current_timezone(),
        )
        next_month_start_dt = timezone.make_aware(
            datetime.combine(next_month_start, time.min),
            timezone.get_current_timezone(),
        )

        remaining_accessories = list(
            Accessory.objects.select_for_update()
            .filter(
                branch=branch,
                is_deleted=False,
                is_month_closed=False,
                stock__gt=0,
                added_at__gte=month_start_dt,
                added_at__lt=next_month_start_dt,
            )
            .order_by("id")
        )

        accessories_recreated = 0
        accessory_rollover_amount = Decimal("0")

        for accessory in remaining_accessories:
            already_rolled = Accessory.objects.filter(
                rolled_over_from=accessory,
                is_deleted=False,
            ).exists()

            remaining_stock = accessory.stock

            accessory.is_month_closed = True
            accessory.month_closed_at = now
            accessory.save(update_fields=["is_month_closed", "month_closed_at", "updated_at"])

            if not already_rolled:
                Accessory.objects.create(
                    name=accessory.name,
                    category_id=accessory.category_id,
                    branch_id=accessory.branch_id,
                    unit_cost=accessory.unit_cost,
                    stock=remaining_stock,
                    added_by_id=accessory.added_by_id,
                    is_active=True,
                    rolled_over_from=accessory,
                )
                accessories_recreated += 1
                accessory_rollover_amount += remaining_stock * accessory.unit_cost

        if accessory_rollover_amount > 0:
            capital = CapitalService.get_accessory_capital(branch, next_month_start)
            CapitalService.add_invested_amount_only(capital, accessory_rollover_amount)

        return accessories_recreated, accessory_rollover_amount

    @staticmethod
    def _lock_branch(branch):
        return Branch.objects.select_for_update().select_related("owner").get(pk=branch.pk)

    @staticmethod
    def _get_closing_record(*, branch, closing_month):
        return (
            MonthClosingRecord.objects.select_for_update()
            .filter(
                branch=branch,
                month=closing_month,
                is_deleted=False,
            )
            .first()
        )

    @staticmethod
    def _get_dashboard_snapshot(*, branch, closing_month):
        return DashboardSnapshot.objects.filter(
            branch=branch,
            month=closing_month,
        ).first()

    @staticmethod
    def _record_blocks_execution(record, *, snapshot_exists):
        if record is None:
            return False
        if record.status == MonthClosingRecord.STATUS_COMPLETED:
            return snapshot_exists
        if record.status == MonthClosingRecord.STATUS_STARTED:
            return not MonthClosingService._is_started_record_stale(record)
        return False

    @staticmethod
    def _is_started_record_stale(record, now=None):
        if record is None or record.status != MonthClosingRecord.STATUS_STARTED:
            return False

        now = now or timezone.now()
        started_at = record.started_at or record.added_at
        if started_at is None:
            return True
        if timezone.is_naive(started_at):
            started_at = timezone.make_aware(
                started_at,
                timezone.get_current_timezone(),
            )
        return now - started_at > STARTED_RECORD_STALE_AFTER

    @staticmethod
    def _prepare_closing_record(*, branch, closing_month):
        now = timezone.now()

        with transaction.atomic():
            record = MonthClosingService._get_closing_record(
                branch=branch,
                closing_month=closing_month,
            )
            snapshot_exists = DashboardSnapshot.objects.filter(
                branch=branch,
                month=closing_month,
            ).exists()
            if MonthClosingService._record_blocks_execution(
                record,
                snapshot_exists=snapshot_exists,
            ):
                return None

            if record is None:
                try:
                    with transaction.atomic():
                        return MonthClosingRecord.objects.create(
                            branch=branch,
                            month=closing_month,
                            status=MonthClosingRecord.STATUS_STARTED,
                            started_at=now,
                            completed_at=None,
                            phones_closed=0,
                            phones_recreated=0,
                            accessories_processed=0,
                            accessories_recreated=0,
                            debt_adjustment_applied=False,
                            debt_adjustment_amount=Decimal("0"),
                            phone_rollover_applied=False,
                            phone_rollover_amount=Decimal("0"),
                            accessory_rollover_applied=False,
                            accessory_rollover_amount=Decimal("0"),
                        )
                except IntegrityError:
                    record = MonthClosingService._get_closing_record(
                        branch=branch,
                        closing_month=closing_month,
                    )
                    snapshot_exists = DashboardSnapshot.objects.filter(
                        branch=branch,
                        month=closing_month,
                    ).exists()
                    if MonthClosingService._record_blocks_execution(
                        record,
                        snapshot_exists=snapshot_exists,
                    ):
                        return None
                    if record is None:
                        raise

            record.status = MonthClosingRecord.STATUS_STARTED
            record.started_at = now
            record.completed_at = None
            record.phones_closed = 0
            record.phones_recreated = 0
            record.accessories_processed = 0
            record.accessories_recreated = 0
            record.debt_adjustment_applied = False
            record.debt_adjustment_amount = Decimal("0")
            record.phone_rollover_applied = False
            record.phone_rollover_amount = Decimal("0")
            record.accessory_rollover_applied = False
            record.accessory_rollover_amount = Decimal("0")
            record.save(
                update_fields=[
                    "status",
                    "started_at",
                    "completed_at",
                    "phones_closed",
                    "phones_recreated",
                    "accessories_processed",
                    "accessories_recreated",
                    "debt_adjustment_applied",
                    "debt_adjustment_amount",
                    "phone_rollover_applied",
                    "phone_rollover_amount",
                    "accessory_rollover_applied",
                    "accessory_rollover_amount",
                    "updated_at",
                ]
            )
            return record

    @staticmethod
    def _calculate_snapshot_payload(*, branch, closing_month):
        return DashboardService.build_month_snapshot(
            branch=branch,
            month=closing_month,
        )

    @staticmethod
    def _persist_dashboard_snapshot(*, branch, closing_month, payload):
        snapshot, created = DashboardSnapshot.objects.update_or_create(
            branch=branch,
            month=closing_month,
            defaults={
                "dashboard_data": payload["dashboard_data"],
                "phone_data": payload["phone_data"],
                "accessory_data": payload["accessory_data"],
                "debt_data": payload["debt_data"],
                "expense_data": payload["expense_data"],
                "salary_data": payload["salary_data"],
                "capital_data": payload["capital_data"],
                "is_locked": True,
            },
        )
        return snapshot, created

    @staticmethod
    def _populate_result_from_payload(*, result, payload):
        result.phones_closed = 0
        result.phones_recreated = 0
        result.accessories_processed = 0
        result.phone_inventory_value = Decimal("0")
        result.accessory_inventory_value = Decimal("0")
        result.dashboard_data = payload["dashboard_data"]
        result.phone_data = payload["phone_data"]
        result.accessory_data = payload["accessory_data"]
        result.debt_data = payload["debt_data"]
        result.expense_data = payload["expense_data"]
        result.salary_data = payload["salary_data"]
        result.capital_data = payload["capital_data"]

    @staticmethod
    def _get_dry_run_snapshot_action(*, record, snapshot):
        snapshot_exists = snapshot is not None
        if MonthClosingService._record_blocks_execution(
            record,
            snapshot_exists=snapshot_exists,
        ):
            return "would_skip"
        return "would_update" if snapshot_exists else "would_create"

    @staticmethod
    def _mark_closing_record_completed(*, record_id, result):
        completed_at = timezone.now()
        record = MonthClosingRecord.objects.select_for_update().get(pk=record_id)
        record.status = MonthClosingRecord.STATUS_COMPLETED
        record.completed_at = completed_at
        record.phones_closed = result.phones_closed
        record.phones_recreated = result.phones_recreated
        record.accessories_processed = result.accessories_processed
        record.accessories_recreated = result.accessories_recreated
        record.debt_adjustment_applied = False
        record.debt_adjustment_amount = Decimal("0")
        record.phone_rollover_applied = True
        record.phone_rollover_amount = result.phone_rollover_amount
        record.accessory_rollover_applied = True
        record.accessory_rollover_amount = result.accessory_rollover_amount
        record.save(
            update_fields=[
                "status",
                "completed_at",
                "phones_closed",
                "phones_recreated",
                "accessories_processed",
                "accessories_recreated",
                "debt_adjustment_applied",
                "debt_adjustment_amount",
                "phone_rollover_applied",
                "phone_rollover_amount",
                "accessory_rollover_applied",
                "accessory_rollover_amount",
                "updated_at",
            ]
        )

    @staticmethod
    def _mark_closing_record_failed(*, record_id):
        with transaction.atomic():
            record = (
                MonthClosingRecord.objects.select_for_update()
                .filter(pk=record_id, is_deleted=False)
                .first()
            )
            if record is None or record.status == MonthClosingRecord.STATUS_COMPLETED:
                return

            record.status = MonthClosingRecord.STATUS_FAILED
            record.completed_at = None
            record.save(update_fields=["status", "completed_at", "updated_at"])

    @staticmethod
    def _log_skip(*, branch, closing_month, record):
        if record and record.status == MonthClosingRecord.STATUS_STARTED:
            logger.info(
                "Filial #%s uchun %s oyi yopilishi hozir ishlanmoqda",
                branch.id,
                closing_month,
            )
            return

        logger.info(
            "Filial #%s uchun %s oyi allaqachon yopilgan",
            branch.id,
            closing_month,
        )


class MonthCloseService:
    @staticmethod
    def close_month(*, dry_run=False, reference_time=None, batch_size=DEFAULT_BATCH_SIZE, month=None):
        if not dry_run:
            MonthCloseService._try_backup(reference_time=reference_time, month=month)
        results = list(
            MonthClosingService.close_all_branches(
                dry_run=dry_run,
                reference_time=reference_time,
                batch_size=batch_size,
                month=month,
            )
        )
        return results

    @staticmethod
    def _try_backup(*, reference_time=None, month=None):
        backup_dir = getattr(settings, "MONTH_CLOSE_BACKUP_DIR", None)
        if not backup_dir:
            logger.warning(
                "Automatic DB backup before month close is not configured; skipping backup step."
            )
            return None

        now = timezone.localtime(reference_time or timezone.now())
        period = MonthClosingService.resolve_period(reference_time=reference_time, month=month)
        backup_dir_path = Path(backup_dir)
        backup_dir_path.mkdir(parents=True, exist_ok=True)
        backup_path = backup_dir_path / (
            f"month_close_{period['closing_month'].isoformat()}_{now.strftime('%Y%m%d_%H%M%S')}.json"
        )

        try:
            with backup_path.open("w", encoding="utf-8") as backup_file:
                call_command("dumpdata", stdout=backup_file)
        except Exception:
            logger.warning(
                "Automatic DB backup before month close failed; continuing without backup.",
                exc_info=True,
            )
            return None

        logger.info("Month-close backup created: %s", backup_path)
        return str(backup_path)
