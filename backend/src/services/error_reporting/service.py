from django.db import transaction
from django.utils import timezone

from src.core.models import ErrorReport, ValidationErrorCounter
from src.services.error_reporting.fingerprint import compute_fingerprint
from src.services.error_reporting.telegram import TelegramNotifier


class ErrorReportingService:
    @staticmethod
    def report_error(
        *,
        source,
        error_type,
        error_message,
        severity="ERROR",
        kind="EXCEPTION",
        stack_trace=None,
        request_path=None,
        request_method=None,
        status_code=None,
        user=None,
        app_version=None,
        platform=None,
        context=None,
    ):
        fp = compute_fingerprint(source, error_type, request_path, status_code, kind)
        now = timezone.now()

        with transaction.atomic():
            existing = (
                ErrorReport.objects.select_for_update()
                .filter(fingerprint=fp, is_deleted=False)
                .first()
            )
            if existing:
                existing.occurrence_count += 1
                existing.last_seen_at = now
                existing.save(update_fields=["occurrence_count", "last_seen_at", "updated_at"])
                report = existing
            else:
                report = ErrorReport.objects.create(
                    source=source,
                    severity=severity,
                    kind=kind,
                    error_type=error_type,
                    error_message=error_message,
                    stack_trace=stack_trace,
                    request_path=request_path,
                    request_method=request_method,
                    status_code=status_code,
                    user=user,
                    app_version=app_version,
                    platform=platform,
                    context=context or {},
                    fingerprint=fp,
                    first_seen_at=now,
                    last_seen_at=now,
                )

        if _should_notify(report):
            try:
                TelegramNotifier().send_error_report(report)
                report.notified_at = now
                report.save(update_fields=["notified_at", "updated_at"])
            except Exception:
                pass

        return report

    @staticmethod
    def track_user_validation_error(
        *,
        user,
        error_type,
        request_path,
        error_message="",
        threshold=10,
        window_minutes=30,
    ):
        now = timezone.now()
        window_cutoff = now - timezone.timedelta(minutes=window_minutes)
        should_alert = False
        alert_count = 0

        with transaction.atomic():
            try:
                counter = ValidationErrorCounter.objects.select_for_update().get(
                    user=user,
                    error_type=error_type,
                    request_path=request_path,
                )
            except ValidationErrorCounter.DoesNotExist:
                counter = ValidationErrorCounter(
                    user=user,
                    error_type=error_type,
                    request_path=request_path,
                    window_start=now,
                    count=0,
                )

            if counter.window_start < window_cutoff:
                counter.count = 0
                counter.window_start = now
                counter.last_notified_at = None

            counter.count += 1

            if counter.count >= threshold and counter.last_notified_at is None:
                should_alert = True
                alert_count = counter.count
                counter.last_notified_at = now

            counter.save()

        if should_alert:
            ErrorReportingService.report_error(
                source="BACKEND",
                error_type=error_type,
                error_message=error_message or f"Validation threshold {threshold}x reached",
                severity="WARNING",
                kind="VALIDATION",
                request_path=request_path,
                user=user,
                context={"threshold": threshold, "count": alert_count},
            )


def _should_notify(report):
    if report.severity == ErrorReport.Severity.CRITICAL:
        return True
    if report.occurrence_count == 1:
        return True
    if report.occurrence_count in (10, 100, 1000):
        return True
    if report.notified_at:
        delta = timezone.now() - report.notified_at
        if delta.total_seconds() < 300:
            return False
    return False
