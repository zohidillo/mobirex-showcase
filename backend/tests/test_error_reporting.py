import logging
from datetime import timedelta
from unittest.mock import MagicMock, patch

import pytest
from django.test import override_settings
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from src.core.models import ErrorReport, ValidationErrorCounter
from src.services.error_reporting import ErrorReportingService
from src.services.error_reporting.logging_handler import TelegramLoggingHandler
from src.services.error_reporting.telegram import TelegramNotifier

pytestmark = pytest.mark.django_db


# ──────────────────────────── fixtures ────────────────────────────


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def owner(db):
    from src.core.models import User
    return User.objects.create_user(username="er_owner", password="pass")


@pytest.fixture
def authed_client(api_client, owner):
    api_client.force_authenticate(user=owner)
    return api_client


@pytest.fixture
def report_url():
    return reverse("api_error_report_create")


def _call(**kwargs):
    defaults = {
        "source": "BACKEND",
        "error_type": "TestError",
        "error_message": "test message",
    }
    defaults.update(kwargs)
    return ErrorReportingService.report_error(**defaults)


# ──────────────────────────── service: DB ────────────────────────────


def test_report_error_creates_new_record(db):
    report = _call()
    assert ErrorReport.objects.filter(pk=report.pk).exists()
    assert report.occurrence_count == 1
    assert report.source == "BACKEND"


def test_report_error_duplicate_increments_count(db):
    _call()
    _call()
    reports = ErrorReport.objects.all()
    assert reports.count() == 1
    assert reports.first().occurrence_count == 2


def test_fingerprint_differs_by_path(db):
    _call(request_path="/api/phones/")
    _call(request_path="/api/accessories/")
    assert ErrorReport.objects.count() == 2


def test_fingerprint_differs_by_status(db):
    _call(request_path="/api/phones/", status_code=400)
    _call(request_path="/api/phones/", status_code=500)
    assert ErrorReport.objects.count() == 2


# ──────────────────────────── service: notifications ────────────────────────────


def test_first_occurrence_notifies(db):
    with patch.object(TelegramNotifier, "send_error_report") as mock_send:
        _call()
    mock_send.assert_called_once()


def test_milestone_notifies(db):
    with patch.object(TelegramNotifier, "send_error_report") as mock_send:
        for _ in range(10):
            _call()
    calls = mock_send.call_count
    # count=1 → notify, count=10 → notify
    assert calls >= 2
    last_report = ErrorReport.objects.first()
    assert last_report.occurrence_count == 10


def test_non_milestone_skips(db):
    _call()  # count=1, notified
    with patch.object(TelegramNotifier, "send_error_report") as mock_send:
        for _ in range(4):  # count 2..5
            _call()
    mock_send.assert_not_called()


def test_critical_always_notifies(db):
    with patch.object(TelegramNotifier, "send_error_report") as mock_send:
        for _ in range(3):
            _call(severity="CRITICAL")
    assert mock_send.call_count == 3


def test_rate_limit_within_5_minutes(db):
    with patch.object(TelegramNotifier, "send_error_report") as mock_send:
        _call()               # count=1 → notify
        _call()               # count=2 → rate limited (< 5 min)
    assert mock_send.call_count == 1


def test_telegram_disabled_no_send(db):
    with override_settings(TELEGRAM_NOTIFICATIONS_ENABLED=False):
        with patch.object(TelegramNotifier, "_post") as mock_post:
            _call()
    mock_post.assert_not_called()
    assert ErrorReport.objects.count() == 1


def test_telegram_network_error_does_not_raise(db):
    with patch.object(TelegramNotifier, "_post", side_effect=ConnectionError("no network")):
        report = _call()
    assert report is not None
    assert ErrorReport.objects.count() == 1


# ──────────────────────────── logging handler ────────────────────────────


def test_logging_handler_writes_report(db):
    handler = TelegramLoggingHandler()
    handler.setLevel(logging.ERROR)
    log = logging.getLogger("django.test.handler")
    log.addHandler(handler)
    try:
        with patch.object(TelegramNotifier, "send_error_report"):
            log.error("Something broke in handler test")
    finally:
        log.removeHandler(handler)
    assert ErrorReport.objects.filter(error_type="ERROR").exists()


def test_logging_handler_skips_own_recursion(db):
    handler = TelegramLoggingHandler()
    record = logging.LogRecord(
        name="src.services.error_reporting.service",
        level=logging.ERROR,
        pathname="",
        lineno=0,
        msg="recursion guard",
        args=(),
        exc_info=None,
    )
    with patch.object(TelegramNotifier, "send_error_report") as mock_send:
        handler.emit(record)
    mock_send.assert_not_called()
    assert ErrorReport.objects.count() == 0


def test_celery_source_when_logger_starts_with_celery(db):
    handler = TelegramLoggingHandler()
    record = logging.LogRecord(
        name="celery.task.my_task",
        level=logging.ERROR,
        pathname="",
        lineno=0,
        msg="celery task failed",
        args=(),
        exc_info=None,
    )
    with patch.object(TelegramNotifier, "send_error_report"):
        handler.emit(record)
    report = ErrorReport.objects.first()
    assert report is not None
    assert report.source == ErrorReport.Source.BACKEND_CELERY


# ──────────────────────────── API endpoint ────────────────────────────


def test_api_unauthenticated_returns_401(api_client, report_url):
    res = api_client.post(report_url, {"error_type": "X", "error_message": "y"}, format="json")
    assert res.status_code == 401


def test_api_authenticated_creates_report(authed_client, owner, report_url):
    with patch.object(TelegramNotifier, "send_error_report"):
        res = authed_client.post(
            report_url,
            {"error_type": "DioException", "error_message": "network fail"},
            format="json",
        )
    assert res.status_code == 201
    assert res.json()["data"]["received"] is True
    report = ErrorReport.objects.first()
    assert report is not None
    assert report.user_id == owner.pk


def test_api_rate_limit_30_per_minute(authed_client, report_url):
    from django.core.cache import cache
    from rest_framework.throttling import SimpleRateThrottle

    cache.clear()
    payload = {"error_type": "RateTest", "error_message": "spam"}
    with patch.object(SimpleRateThrottle, "THROTTLE_RATES", {"error_report": "3/min"}):
        with patch.object(TelegramNotifier, "send_error_report"):
            for _ in range(3):
                res = authed_client.post(report_url, payload, format="json")
                assert res.status_code == 201
            res = authed_client.post(report_url, payload, format="json")
    assert res.status_code == 429


def test_api_platform_android_sets_correct_source(authed_client, report_url):
    with patch.object(TelegramNotifier, "send_error_report"):
        authed_client.post(
            report_url,
            {"error_type": "E", "error_message": "m", "platform": "android"},
            format="json",
        )
    report = ErrorReport.objects.first()
    assert report.source == ErrorReport.Source.MOBILE_ANDROID


def test_api_platform_ios_sets_correct_source(authed_client, report_url):
    with patch.object(TelegramNotifier, "send_error_report"):
        authed_client.post(
            report_url,
            {"error_type": "E", "error_message": "m", "platform": "ios"},
            format="json",
        )
    report = ErrorReport.objects.first()
    assert report.source == ErrorReport.Source.MOBILE_IOS


# ──────────────────────────── ValidationErrorCounter ────────────────────────────


def test_track_validation_error_creates_counter(db, owner):
    ErrorReportingService.track_user_validation_error(
        user=owner,
        error_type="RequiredField",
        request_path="/api/phones/",
    )
    counter = ValidationErrorCounter.objects.get(
        user=owner, error_type="RequiredField", request_path="/api/phones/"
    )
    assert counter.count == 1


def test_track_validation_error_increments_within_window(db, owner):
    with patch.object(TelegramNotifier, "send_error_report") as mock_send:
        for _ in range(5):
            ErrorReportingService.track_user_validation_error(
                user=owner,
                error_type="RequiredField",
                request_path="/api/phones/",
                threshold=10,
            )
    counter = ValidationErrorCounter.objects.get(
        user=owner, error_type="RequiredField", request_path="/api/phones/"
    )
    assert counter.count == 5
    mock_send.assert_not_called()


def test_track_validation_error_notifies_at_threshold(db, owner):
    with patch.object(TelegramNotifier, "send_error_report") as mock_send:
        for _ in range(10):
            ErrorReportingService.track_user_validation_error(
                user=owner,
                error_type="RequiredField",
                request_path="/api/phones/",
                threshold=10,
            )
    mock_send.assert_called_once()
    counter = ValidationErrorCounter.objects.get(
        user=owner, error_type="RequiredField", request_path="/api/phones/"
    )
    assert counter.last_notified_at is not None


def test_track_validation_error_window_reset(db, owner):
    old_time = timezone.now() - timedelta(minutes=60)
    counter = ValidationErrorCounter.objects.create(
        user=owner,
        error_type="RequiredField",
        request_path="/api/phones/",
        count=9,
        window_start=old_time,
        last_notified_at=None,
    )
    with patch.object(TelegramNotifier, "send_error_report"):
        ErrorReportingService.track_user_validation_error(
            user=owner,
            error_type="RequiredField",
            request_path="/api/phones/",
            threshold=10,
            window_minutes=30,
        )
    counter.refresh_from_db()
    assert counter.count == 1
    assert counter.last_notified_at is None


def test_month_closing_logger_routes_to_telegram(db):
    handler = TelegramLoggingHandler()
    handler.setLevel(logging.ERROR)
    log = logging.getLogger("month_closing")
    log.addHandler(handler)
    try:
        with patch.object(TelegramNotifier, "send_error_report"):
            log.error("Filial #1 uchun yopishda xatolik: something failed")
    finally:
        log.removeHandler(handler)
    report = ErrorReport.objects.filter(error_type="ERROR").first()
    assert report is not None
    assert report.source == ErrorReport.Source.BACKEND
