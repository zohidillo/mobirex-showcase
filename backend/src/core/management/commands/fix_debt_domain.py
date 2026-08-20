from datetime import datetime, time, timedelta

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from src.core import models


def _parse_required_date(raw_value, option_name):
    if not raw_value:
        raise CommandError(f"`{option_name}` kiritilishi shart.")
    try:
        return datetime.strptime(raw_value, "%Y-%m-%d").date()
    except ValueError as exc:
        raise CommandError(f"`{option_name}` YYYY-MM-DD formatida bo‘lishi kerak.") from exc


def _make_aware_range(start_date, end_date):
    start_dt = timezone.make_aware(datetime.combine(start_date, time.min))
    end_dt = timezone.make_aware(datetime.combine(end_date + timedelta(days=1), time.min))
    return start_dt, end_dt


class Command(BaseCommand):
    help = "Berilgan sana oralig‘idagi qarzlar uchun domain qiymatini tuzatadi."

    def add_arguments(self, parser):
        parser.add_argument(
            "--start-date",
            type=str,
            required=True,
            help="Boshlanish sanasi. Misol: 2026-03-01",
        )
        parser.add_argument(
            "--end-date",
            type=str,
            required=True,
            help="Tugash sanasi. Misol: 2026-03-31",
        )
        parser.add_argument(
            "--domain",
            type=str,
            default=models.Debt.DOMAIN_PHONE,
            choices=[models.Debt.DOMAIN_PHONE, models.Debt.DOMAIN_ACCESSORY],
            help="Qarzlarga beriladigan domain qiymati.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Nechta yozuv yangilanishini ko‘rsatadi, lekin bazaga yozmaydi.",
        )

    def handle(self, *args, **options):
        start_date = _parse_required_date(options["start_date"], "--start-date")
        end_date = _parse_required_date(options["end_date"], "--end-date")
        if end_date < start_date:
            raise CommandError("`--end-date` `--start-date` dan kichik bo‘lishi mumkin emas.")

        target_domain = options["domain"]
        dry_run = options["dry_run"]
        start_dt, end_dt = _make_aware_range(start_date, end_date)

        queryset = models.Debt.objects.filter(
            added_at__gte=start_dt,
            added_at__lt=end_dt,
        ).exclude(domain=target_domain)

        matched_count = queryset.count()
        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f"Dry-run: {matched_count} ta qarz `{target_domain}` ga o‘zgartiriladi."
                )
            )
            return

        with transaction.atomic():
            updated_count = queryset.update(domain=target_domain)

        self.stdout.write(
            self.style.SUCCESS(
                f"Yangilandi: {updated_count} ta qarz `{target_domain}` ga o‘zgartirildi."
            )
        )
