"""
Tests for ErrorReportingMiddleware, BaseAPIView 500 path, and
api_exception_handler validation tracking.
"""

import logging
from unittest.mock import MagicMock, patch

import pytest
from django.core.exceptions import PermissionDenied as DjangoPermissionDenied
from django.core.exceptions import ValidationError as DjangoValidationError
from django.http import Http404, HttpRequest, HttpResponse
from django.test import RequestFactory, override_settings
from rest_framework.exceptions import ValidationError as DRFValidationError
from rest_framework.test import APIClient, APIRequestFactory

from src.api.base import BaseAPIView
from src.api.exception_handler import api_exception_handler
from src.bases.middleware.error_reporting import ErrorReportingMiddleware
from src.core.models import ErrorReport
from src.services.error_reporting.service import ErrorReportingService
from src.services.error_reporting.telegram import TelegramNotifier

pytestmark = pytest.mark.django_db


# ──────────────────────────── helpers ────────────────────────────


def _make_request(path="/some/view/", method="GET", user=None, authenticated=True):
    factory = RequestFactory()
    request = factory.get(path)
    if user is not None:
        request.user = user
    else:
        mock_user = MagicMock()
        mock_user.is_authenticated = authenticated
        if not authenticated:
            mock_user.pk = None
        request.user = mock_user
    return request


def _make_middleware(side_effect=None):
    """Return middleware wrapping a get_response that does nothing (or raises)."""
    def get_response(request):
        if side_effect:
            raise side_effect
        return HttpResponse("ok")
    return ErrorReportingMiddleware(get_response)


# ──────────────────────────── middleware ────────────────────────────


def test_middleware_reports_uncaught_exception(db):
    request = _make_request()
    exc = RuntimeError("boom")
    middleware = _make_middleware()

    with patch.object(ErrorReportingService, "report_error") as mock_report:
        middleware.process_exception(request, exc)

    mock_report.assert_called_once()
    call_kwargs = mock_report.call_args.kwargs
    assert call_kwargs["error_type"] == "RuntimeError"
    assert call_kwargs["source"] == "BACKEND"
    assert call_kwargs["kind"] == "EXCEPTION"


def test_middleware_skips_validation_error(db):
    request = _make_request()
    exc = DjangoValidationError("bad input")

    with patch.object(ErrorReportingService, "report_error") as mock_report:
        _make_middleware().process_exception(request, exc)

    mock_report.assert_not_called()


def test_middleware_skips_permission_denied(db):
    request = _make_request()
    exc = DjangoPermissionDenied("no access")

    with patch.object(ErrorReportingService, "report_error") as mock_report:
        _make_middleware().process_exception(request, exc)

    mock_report.assert_not_called()


def test_middleware_skips_http404(db):
    request = _make_request()
    exc = Http404()

    with patch.object(ErrorReportingService, "report_error") as mock_report:
        _make_middleware().process_exception(request, exc)

    mock_report.assert_not_called()


def test_middleware_sets_user_from_request(db):
    from src.core.models import User
    user = User.objects.create_user(username="mw_user", password="pass")
    request = _make_request(user=user)
    exc = ValueError("something failed")

    with patch.object(ErrorReportingService, "report_error") as mock_report:
        _make_middleware().process_exception(request, exc)

    call_kwargs = mock_report.call_args.kwargs
    assert call_kwargs["user"] == user


def test_middleware_handles_anonymous_user(db):
    request = _make_request(authenticated=False)
    exc = ValueError("anon error")

    with patch.object(ErrorReportingService, "report_error") as mock_report:
        _make_middleware().process_exception(request, exc)

    call_kwargs = mock_report.call_args.kwargs
    assert call_kwargs["user"] is None


def test_middleware_does_not_break_response(db):
    """If ErrorReportingService itself crashes, process_exception returns None
    (Django continues to its 500 handler) — no secondary exception raised."""
    request = _make_request()
    exc = RuntimeError("original error")

    with patch.object(
        ErrorReportingService, "report_error", side_effect=Exception("service down")
    ):
        result = _make_middleware().process_exception(request, exc)

    assert result is None


# ──────────────────────────── BaseAPIView 500 path ────────────────────────────


class _BrokenView(BaseAPIView):
    """Test view that always raises a RuntimeError."""

    def get(self, request):
        raise RuntimeError("db is gone")


def test_api_view_500_reports_to_telegram(db):
    factory = APIRequestFactory()
    request = factory.get("/api/broken/")

    from src.core.models import User
    user = User.objects.create_user(username="api500_user", password="pass")

    view = _BrokenView.as_view()

    with patch.object(TelegramNotifier, "send_error_report"):
        with patch.object(ErrorReportingService, "report_error", wraps=ErrorReportingService.report_error) as mock_report:
            from rest_framework.request import Request
            from rest_framework_simplejwt.authentication import JWTAuthentication
            drf_request = Request(request)
            drf_request._user = user
            view_instance = _BrokenView()
            view_instance.request = drf_request
            view_instance.handle_exception(RuntimeError("db is gone"))

    mock_report.assert_called_once()
    call_kwargs = mock_report.call_args.kwargs
    assert call_kwargs["status_code"] == 500
    assert call_kwargs["error_type"] == "RuntimeError"
    assert call_kwargs["source"] == "BACKEND"


def test_api_view_validation_does_not_report_500(db):
    """ValidationError → 400, must NOT reach the 500 reporting branch."""
    from rest_framework.request import Request

    factory = APIRequestFactory()
    raw_request = factory.get("/api/test/")
    drf_request = Request(raw_request)
    mock_user = MagicMock()
    mock_user.is_authenticated = True
    drf_request._user = mock_user

    view_instance = _BrokenView()
    view_instance.request = drf_request

    with patch.object(ErrorReportingService, "report_error") as mock_report:
        response = view_instance.handle_exception(DRFValidationError("bad field"))

    mock_report.assert_not_called()
    assert response.status_code == 400


def test_api_view_500_response_shape_unchanged(db):
    """500 path must still return {"success": false, "error": "..."} shape."""
    from rest_framework.request import Request

    factory = APIRequestFactory()
    raw_request = factory.get("/api/test/")
    drf_request = Request(raw_request)
    mock_user = MagicMock()
    mock_user.is_authenticated = True
    drf_request._user = mock_user

    view_instance = _BrokenView()
    view_instance.request = drf_request

    with patch.object(TelegramNotifier, "send_error_report"):
        response = view_instance.handle_exception(RuntimeError("crash"))

    assert response.status_code == 500
    import json
    body = json.loads(response.content)
    assert body["success"] is False
    assert "error" in body


# ──────────────────────────── exception_handler ────────────────────────────


def test_exception_handler_tracks_validation_for_authenticated_user(db):
    from src.core.models import User
    user = User.objects.create_user(username="eh_user", password="pass")

    mock_request = MagicMock()
    mock_request.path = "/api/phones/"
    mock_request.user = user
    # user.is_authenticated is a property — real User is always authenticated

    exc = DRFValidationError({"field": ["required"]})
    context = {"request": mock_request, "view": None}

    with patch.object(ErrorReportingService, "track_user_validation_error") as mock_track:
        with patch("src.api.exception_handler.drf_exception_handler") as mock_drf:
            mock_drf.return_value = MagicMock(status_code=400)
            api_exception_handler(exc, context)

    mock_track.assert_called_once()
    call_kwargs = mock_track.call_args.kwargs
    assert call_kwargs["user"] == user
    assert call_kwargs["request_path"] == "/api/phones/"


def test_exception_handler_skips_anonymous_validation(db):
    mock_request = MagicMock()
    mock_request.path = "/api/phones/"
    mock_user = MagicMock()
    mock_user.is_authenticated = False
    mock_request.user = mock_user

    exc = DRFValidationError({"field": ["required"]})
    context = {"request": mock_request, "view": None}

    with patch.object(ErrorReportingService, "track_user_validation_error") as mock_track:
        with patch("src.api.exception_handler.drf_exception_handler") as mock_drf:
            mock_drf.return_value = MagicMock(status_code=400)
            api_exception_handler(exc, context)

    mock_track.assert_not_called()


def test_exception_handler_returns_unchanged_response(db):
    """Non-validation exception: response passes through unchanged."""
    from rest_framework.exceptions import NotFound

    mock_request = MagicMock()
    mock_request.user.is_authenticated = True

    exc = NotFound("not found")
    context = {"request": mock_request, "view": None}
    fake_response = MagicMock(status_code=404)

    with patch("src.api.exception_handler.drf_exception_handler", return_value=fake_response):
        result = api_exception_handler(exc, context)

    assert result is fake_response


def test_exception_handler_silent_on_tracking_failure(db):
    """If track_user_validation_error crashes, response is still returned."""
    from src.core.models import User
    user = User.objects.create_user(username="eh_silent_user", password="pass")

    mock_request = MagicMock()
    mock_request.path = "/api/phones/"
    mock_request.user = user
    # user.is_authenticated is a property — real User is always authenticated

    exc = DRFValidationError({"x": ["y"]})
    context = {"request": mock_request, "view": None}
    fake_response = MagicMock(status_code=400)

    with patch.object(
        ErrorReportingService,
        "track_user_validation_error",
        side_effect=Exception("db down"),
    ):
        with patch("src.api.exception_handler.drf_exception_handler", return_value=fake_response):
            result = api_exception_handler(exc, context)

    assert result is fake_response
