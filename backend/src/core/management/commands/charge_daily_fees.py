import logging
from datetime import datetime

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from src.services.billing import DailyChargeService


logger = logging.getLogger("billing")


class Command(BaseCommand):
    help = "Foydalanuvchilardan kunlik to‘lovni yechadi."

    def add_arguments(self, parser):
        parser.add_argument(
            "--chunk-size",
            type=int,
            default=500,
            help="Bir iteratsiyada qayta ishlanadigan foydalanuvchilar soni.",
        )
        parser.add_argument(
            "--charge-at",
            type=str,
            help="ISO formatdagi vaqt. Bo‘sh bo‘lsa hozirgi vaqt ishlatiladi.",
        )

    def _parse_charge_at(self, value):
        if not value:
            return timezone.now()
        try:
            charge_at = datetime.fromisoformat(value)
        except ValueError as exc:
            raise CommandError("`--charge-at` ISO formatda bo‘lishi kerak.") from exc
        if timezone.is_naive(charge_at):
            charge_at = timezone.make_aware(charge_at)
        return charge_at

    def handle(self, *args, **options):
        charge_at = self._parse_charge_at(options.get("charge_at"))
        chunk_size = options["chunk_size"]
        summary = {
            "total": 0,
            "charged": 0,
            "vip": 0,
            "blocked": 0,
            "duplicate": 0,
            "errors": 0,
            "other_skipped": 0,
        }

        self.stdout.write(
            f"Kunlik yechim boshlandi: {timezone.localtime(charge_at).strftime('%Y-%m-%d %H:%M:%S')}"
        )

        for result in DailyChargeService.iter_charge_results(
            charge_at=charge_at,
            chunk_size=chunk_size,
        ):
            summary["total"] += 1
            if result.charged:
                summary["charged"] += 1
                logger.info(
                    "Kunlik yechim bajarildi | user_id=%s | old_balance=%s | new_balance=%s | status=%s",
                    result.user_id,
                    result.balance_before,
                    result.balance_after,
                    result.status,
                )
                continue

            if result.skipped_reason == "error":
                summary["errors"] += 1
                logger.error(
                    "Kunlik yechimda xatolik | user_id=%s | error=%s",
                    result.user_id,
                    result.error,
                )
            elif result.skipped_reason == "vip":
                summary["vip"] += 1
            elif result.skipped_reason == "blocked":
                summary["blocked"] += 1
            elif result.skipped_reason == "duplicate":
                summary["duplicate"] += 1
            else:
                summary["other_skipped"] += 1

        message = (
            "Kunlik yechim yakunlandi | "
            f"jami={summary['total']} | "
            f"yechildi={summary['charged']} | "
            f"vip={summary['vip']} | "
            f"bloklangan={summary['blocked']} | "
            f"takror={summary['duplicate']} | "
            f"xatolar={summary['errors']} | "
            f"boshqa={summary['other_skipped']}"
        )
        logger.info(message)
        self.stdout.write(self.style.SUCCESS(message))
