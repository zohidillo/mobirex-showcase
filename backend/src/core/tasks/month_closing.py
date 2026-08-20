import logging

try:
    from celery import shared_task
except ImportError:  # pragma: no cover
    def shared_task(*args, **kwargs):
        def decorator(func):
            return func

        return decorator

from src.services.month_closing import MonthCloseService


logger = logging.getLogger("month_closing")


def _serialize_result(result):
    return {
        "branch_id": result.branch_id,
        "month": result.month.isoformat(),
        "skipped": result.skipped,
        "snapshot_action": result.snapshot_action,
        "phones_closed": result.phones_closed,
        "phones_recreated": result.phones_recreated,
        "phone_rollover_amount": str(result.phone_rollover_amount),
        "accessories_processed": result.accessories_processed,
        "accessories_recreated": result.accessories_recreated,
        "accessory_rollover_amount": str(result.accessory_rollover_amount),
        "error": result.error,
    }


def _run_month_close():
    results = []

    for result in MonthCloseService.close_month(dry_run=False):
        results.append(_serialize_result(result))

        if result.error:
            logger.error(
                "Filial #%s uchun yopishda xatolik: %s",
                result.branch_id,
                result.error,
            )
        elif result.skipped or result.snapshot_action == "skipped":
            logger.info("Filial #%s uchun oy yopilishi o'tkazib yuborildi", result.branch_id)
        else:
            logger.info(
                "Filial #%s uchun oy yopildi (%s): %d telefon, %d aksessuar ko'chirildi",
                result.branch_id,
                result.snapshot_action,
                result.phones_recreated,
                result.accessories_recreated,
            )

    return results


@shared_task(name="src.core.tasks.month_closing.run_month_close_task")
def run_month_close_task():
    return _run_month_close()


@shared_task(name="src.core.tasks.month_closing.run_month_closing")
def run_month_closing():
    return _run_month_close()
