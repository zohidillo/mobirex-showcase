import logging
from argparse import BooleanOptionalAction
from datetime import date, datetime, time
from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db import connection, transaction
from django.db.models import DecimalField, F, Max, Q, Sum, Value
from django.db.models.functions import Coalesce
from django.utils import timezone

from src.core import models


logger = logging.getLogger(__name__)
DECIMAL_FIELD = DecimalField(max_digits=14, decimal_places=2)


def _parse_month(raw_value, option_name):
    if not raw_value:
        raise CommandError(f"`{option_name}` kiritilishi shart.")
    try:
        parsed = datetime.strptime(raw_value, "%Y-%m")
    except ValueError as exc:
        raise CommandError(f"`{option_name}` YYYY-MM formatida bo‘lishi kerak.") from exc
    return date(parsed.year, parsed.month, 1)


def _next_month(month_start):
    if month_start.month == 12:
        return date(month_start.year + 1, 1, 1)
    return date(month_start.year, month_start.month + 1, 1)


def _month_dt(month_start):
    timezone_info = timezone.get_current_timezone()
    return timezone.make_aware(datetime.combine(month_start, time.min), timezone_info)


def _resolve_period_bounds(options):
    month_raw = options.get("month")
    from_raw = options.get("from_month")
    to_raw = options.get("to_month")

    if month_raw and (from_raw or to_raw):
        raise CommandError("`--month` bilan birga `--from/--to` ishlatib bo‘lmaydi.")

    if month_raw:
        month_start = _parse_month(month_raw, "--month")
        return _month_dt(month_start), _month_dt(_next_month(month_start)), month_start.strftime("%Y-%m")

    if not from_raw and not to_raw:
        return None, None, "all"

    if not from_raw or not to_raw:
        raise CommandError("Oraliq uchun `--from` va `--to` ikkalasi ham kiritilishi kerak.")

    from_month = _parse_month(from_raw, "--from")
    to_month = _parse_month(to_raw, "--to")
    if to_month < from_month:
        raise CommandError("`--to` `--from` dan kichik bo‘lishi mumkin emas.")

    return (
        _month_dt(from_month),
        _month_dt(_next_month(to_month)),
        f"{from_month.strftime('%Y-%m')}..{to_month.strftime('%Y-%m')}",
    )


def _resolve_payment_date_field():
    if "paid_at" in {field.name for field in models.DebtPayment._meta.concrete_fields}:
        return "paid_at"
    return "added_at"


def _has_model_closed_at_field():
    return "closed_at" in {field.name for field in models.Debt._meta.concrete_fields}


def _has_debt_closed_at_column():
    table_name = models.Debt._meta.db_table
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT 1
            FROM information_schema.columns
            WHERE table_schema = current_schema()
              AND table_name = %s
              AND column_name = 'closed_at'
            LIMIT 1
            """,
            [table_name],
        )
        return cursor.fetchone() is not None


def _chunked(items, size=500):
    for index in range(0, len(items), size):
        yield items[index : index + size]


class Command(BaseCommand):
    help = "To‘liq yopilgan qarzlar uchun closed_at qiymatini tekshiradi va (force bo‘lsa) tuzatadi."

    def add_arguments(self, parser):
        parser.add_argument(
            "--month",
            type=str,
            help="Bitta oy. Misol: 2026-03",
        )
        parser.add_argument(
            "--from",
            dest="from_month",
            type=str,
            help="Boshlanish oyi. Misol: 2026-01",
        )
        parser.add_argument(
            "--to",
            dest="to_month",
            type=str,
            help="Tugash oyi. Misol: 2026-03",
        )
        parser.add_argument(
            "--dry-run",
            action=BooleanOptionalAction,
            default=True,
            help="Faqat hisoblaydi, DBga yozmaydi (default).",
        )
        parser.add_argument(
            "--force",
            action="store_true",
            help="DBga yozadi va noto‘g‘ri closed_at qiymatlarini tuzatadi.",
        )

    def _log(self, message):
        self.stdout.write(message)
        logger.info(message)

    def _fetch_existing_closed_at_map(self, debt_ids):
        if not debt_ids:
            return {}

        table_name = connection.ops.quote_name(models.Debt._meta.db_table)
        closed_at_map = {}
        with connection.cursor() as cursor:
            for chunk in _chunked(debt_ids):
                placeholders = ",".join(["%s"] * len(chunk))
                cursor.execute(
                    f"SELECT id, closed_at FROM {table_name} WHERE id IN ({placeholders})",
                    chunk,
                )
                for debt_id, closed_at in cursor.fetchall():
                    closed_at_map[debt_id] = closed_at
        return closed_at_map

    def _raw_update_closed_at(self, updates):
        if not updates:
            return 0

        table_name = connection.ops.quote_name(models.Debt._meta.db_table)
        with connection.cursor() as cursor:
            cursor.executemany(
                f"UPDATE {table_name} SET closed_at = %s WHERE id = %s",
                updates,
            )
        return len(updates)

    def handle(self, *args, **options):
        force = bool(options["force"])
        dry_run = bool(options["dry_run"])
        if force:
            dry_run = False
        period_start_dt, period_end_dt, period_label = _resolve_period_bounds(options)
        payment_date_field = _resolve_payment_date_field()
        has_model_closed_at = _has_model_closed_at_field()
        has_db_closed_at = _has_debt_closed_at_column()

        self._log(
            f"Fix debt closed_at boshlandi | mode={'DRY-RUN' if dry_run else 'FORCE'} | period={period_label}"
        )
        self._log(f"Ishlatiladigan payment sana maydoni: debt_payment.{payment_date_field}")

        total_paid_expression = Coalesce(
            Sum("payments__amount", filter=Q(payments__is_deleted=False)),
            Value(Decimal("0.00")),
            output_field=DECIMAL_FIELD,
        )
        closed_at_expression = Max(
            f"payments__{payment_date_field}",
            filter=Q(payments__is_deleted=False),
        )

        annotated_qs = (
            models.Debt.objects.filter(is_deleted=False)
            .only("id", "amount")
            .annotate(
                total_paid=total_paid_expression,
                computed_closed_at=closed_at_expression,
            )
        )
        checked_count = annotated_qs.count()

        closed_qs = annotated_qs.filter(
            total_paid__gte=F("amount"),
            computed_closed_at__isnull=False,
        )
        if period_start_dt and period_end_dt:
            closed_qs = closed_qs.filter(
                computed_closed_at__gte=period_start_dt,
                computed_closed_at__lt=period_end_dt,
            )

        closed_rows = list(closed_qs.values_list("id", "computed_closed_at"))
        closed_debt_count = len(closed_rows)

        update_payload = []
        if has_model_closed_at:
            mismatched = closed_qs.filter(
                Q(closed_at__isnull=True) | ~Q(closed_at=F("computed_closed_at"))
            )
            update_payload = list(mismatched.values_list("computed_closed_at", "id"))
        elif has_db_closed_at:
            debt_ids = [row[0] for row in closed_rows]
            existing_closed_at_map = self._fetch_existing_closed_at_map(debt_ids)
            update_payload = [
                (computed_closed_at, debt_id)
                for debt_id, computed_closed_at in closed_rows
                if existing_closed_at_map.get(debt_id) != computed_closed_at
            ]

        planned_update_count = len(update_payload)
        already_correct_count = closed_debt_count - planned_update_count
        updated_count = 0

        if has_model_closed_at or has_db_closed_at:
            if not dry_run and update_payload:
                with transaction.atomic():
                    if has_model_closed_at:
                        objects = [
                            models.Debt(pk=debt_id, closed_at=closed_at)
                            for closed_at, debt_id in update_payload
                        ]
                        models.Debt.objects.bulk_update(objects, ["closed_at"])
                        updated_count = len(objects)
                    else:
                        updated_count = self._raw_update_closed_at(update_payload)
        else:
            self._log(
                self.style.WARNING(
                    "Debt model/table da `closed_at` maydoni topilmadi. Command audit rejimida ishladi."
                )
            )

        self._log("---- Yakuniy hisobot ----")
        self._log(f"Debt tekshirildi: {checked_count}")
        self._log(f"Yopilgan debt topildi: {closed_debt_count}")
        self._log(f"closed_at yangilanadi: {planned_update_count}")
        self._log(f"closed_at allaqachon to‘g‘ri: {already_correct_count}")
        if dry_run:
            self._log("DRY-RUN: DBga yozilmadi.")
        else:
            self._log(f"closed_at yangilandi: {updated_count}")
            self._log(self.style.SUCCESS("FORCE yakunlandi: closed_at tekshiruvi tugadi."))
