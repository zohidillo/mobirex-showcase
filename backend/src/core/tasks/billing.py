import logging

from django.core.cache import cache
from django.utils import timezone

try:
    from celery import shared_task
except ImportError:  # pragma: no cover
    def shared_task(*args, **kwargs):
        def decorator(func):
            return func

        return decorator

from src.services.billing import DailyChargeService


logger = logging.getLogger("billing")
LOCK_KEY = "billing:daily_charge:lock"
LOCK_TIMEOUT = 60 * 60 * 4


@shared_task(name="src.core.tasks.billing.run_daily_charges")
def run_daily_charges():
    if not cache.add(LOCK_KEY, timezone.now().isoformat(), timeout=LOCK_TIMEOUT):
        logger.warning("Kunlik yechim vazifasi allaqachon ishga tushgan.")
        return {
            "skipped": True,
            "reason": "locked",
        }

    charge_at = timezone.now()
    summary = {
        "total": 0,
        "charged": 0,
        "vip": 0,
        "blocked": 0,
        "duplicate": 0,
        "errors": 0,
        "other_skipped": 0,
    }

    try:
        for result in DailyChargeService.iter_charge_results(charge_at=charge_at):
            summary["total"] += 1
            if result.charged:
                summary["charged"] += 1
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

        logger.info(
            "Kunlik yechim tugadi | jami=%s | yechildi=%s | vip=%s | bloklangan=%s | takror=%s | xatolar=%s | boshqa=%s",
            summary["total"],
            summary["charged"],
            summary["vip"],
            summary["blocked"],
            summary["duplicate"],
            summary["errors"],
            summary["other_skipped"],
        )
        return summary
    finally:
        cache.delete(LOCK_KEY)
