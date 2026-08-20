from datetime import datetime
from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError

from src.services.month_closing import MonthCloseService
from src.services.month_closing.service import DEFAULT_BATCH_SIZE, MonthClosingService


def _parse_month(value):
    try:
        return datetime.strptime(value, "%Y-%m").date().replace(day=1)
    except ValueError as exc:
        raise CommandError("--month qiymati YYYY-MM formatida bo'lishi kerak.") from exc


class Command(BaseCommand):
    help = "Har bir filial uchun oyni yopish jarayonini bajaradi."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Hisob-kitobni sinab ko'radi, lekin bazaga yozmaydi.",
        )
        parser.add_argument(
            "--batch-size",
            type=int,
            default=DEFAULT_BATCH_SIZE,
            help="Yozish va yaratish amallarida ishlatiladigan paket hajmi.",
        )
        parser.add_argument(
            "--month",
            type=_parse_month,
            help="Yopiladigan oy (YYYY-MM). Ko'rsatilmasa oldingi kalendar oy olinadi.",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        batch_size = options["batch_size"]
        month = options.get("month")
        period = MonthClosingService.resolve_period(month=month)
        processed = 0
        skipped = 0
        errors = 0
        snapshots_created = 0
        snapshots_updated = 0
        total_phones_recreated = 0
        total_phone_rollover_amount = Decimal("0")
        total_accessories_recreated = 0
        total_accessory_rollover_amount = Decimal("0")

        self.stdout.write(f"Closing month: {period['closing_month'].isoformat()}")
        self.stdout.write(f"Next month:    {period['next_month_start'].isoformat()}")
        self.stdout.write(f"Dry-run:       {'yes' if dry_run else 'no'}")
        self.stdout.write("")

        for result in MonthCloseService.close_month(
            dry_run=dry_run,
            batch_size=batch_size,
            month=month,
        ):
            processed += 1
            if result.error:
                errors += 1
                self.stderr.write(
                    self.style.ERROR(
                        f"Filial #{result.branch_id} yopilmadi: {result.error}"
                    )
                )
                continue

            if result.snapshot_action in {"created", "would_create"}:
                snapshots_created += 1
            elif result.snapshot_action in {"updated", "would_update"}:
                snapshots_updated += 1

            if result.skipped or result.snapshot_action in {"skipped", "would_skip"}:
                skipped += 1
                self.stdout.write(
                    self.style.WARNING(
                        f"Filial #{result.branch_id} o'tkazib yuborildi"
                    )
                )
                continue

            total_phones_recreated += result.phones_recreated
            total_phone_rollover_amount += result.phone_rollover_amount
            total_accessories_recreated += result.accessories_recreated
            total_accessory_rollover_amount += result.accessory_rollover_amount

            prefix = "Dry-run filial" if result.dry_run else "Filial"
            self.stdout.write(
                self.style.SUCCESS(
                    f"{prefix} #{result.branch_id} ({result.snapshot_action}): "
                    f"{result.phones_recreated} telefon ({result.phone_rollover_amount}), "
                    f"{result.accessories_recreated} aksessuar ({result.accessory_rollover_amount})"
                )
            )

        self.stdout.write("")
        self.stdout.write(f"Branches processed:           {processed}")
        self.stdout.write(
            f"Snapshots {'would be ' if dry_run else ''}created:  {snapshots_created}"
        )
        self.stdout.write(
            f"Snapshots {'would be ' if dry_run else ''}updated:  {snapshots_updated}"
        )
        self.stdout.write(f"Skipped branches:             {skipped}")
        self.stdout.write(f"Failed branches:              {errors}")
        self.stdout.write("")
        self.stdout.write(f"Phones {'would be ' if dry_run else ''}recreated:    {total_phones_recreated}")
        self.stdout.write(f"Phone rollover amount:        {total_phone_rollover_amount}")
        self.stdout.write(f"Accessories {'would be ' if dry_run else ''}recreated: {total_accessories_recreated}")
        self.stdout.write(f"Accessory rollover amount:   {total_accessory_rollover_amount}")
