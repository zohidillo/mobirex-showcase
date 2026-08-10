import logging
import traceback

from django.core.exceptions import PermissionDenied, ValidationError
from django.http import Http404
from django.utils.translation import gettext_lazy as _
from rest_framework.exceptions import (
    AuthenticationFailed,
    MethodNotAllowed,
    NotAuthenticated,
    PermissionDenied as DRFPermissionDenied,
    Throttled,
)
from rest_framework.exceptions import ValidationError as DRFValidationError
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication

from src.api.exceptions import AccountBlocked
from src.api.permissions import IsAccountActive
from src.api.responses import account_blocked_response, error_response, success_response
from src.shared.paginations import StandardPagination


logger = logging.getLogger(__name__)


class BaseAPIView(APIView):
    """Provide standard JSON responses for future APIs."""

    authentication_classes = [JWTAuthentication]
    pagination_class = StandardPagination

    def get_permissions(self):
        """Append billing-block enforcement to each view's own permissions."""
        return [*super().get_permissions(), IsAccountActive()]

    def success(self, data=None, *, status=200):
        """Return a success response."""
        return success_response(data=data, status=status)

    def error(self, message, *, status=400):
        """Return an error response."""
        return error_response(message=message, status=status)

    def get_pagination(self):
        """Return the configured paginator instance."""
        return self.pagination_class()

    def get_validation_message(self, exc):
        """Extract a readable message from a validation error."""
        detail = getattr(exc, "detail", None)
        if isinstance(detail, dict):
            return "; ".join(
                f"{field}: {', '.join(str(message) for message in messages)}"
                if isinstance(messages, (list, tuple))
                else f"{field}: {messages}"
                for field, messages in detail.items()
            )
        if isinstance(detail, (list, tuple)):
            return "; ".join(str(message) for message in detail)
        if detail:
            return str(detail)
        if hasattr(exc, "message_dict"):
            return "; ".join(
                f"{field}: {', '.join(messages)}"
                for field, messages in exc.message_dict.items()
            )
        if hasattr(exc, "messages"):
            return "; ".join(exc.messages)
        return str(exc)

    def handle_exception(self, exc):
        """Convert known exceptions into standard responses."""
        if isinstance(exc, AccountBlocked):
            return account_blocked_response(exc.detail)
        if isinstance(exc, (ValidationError, DRFValidationError)):
            return self.error(self.get_validation_message(exc), status=400)
        if isinstance(exc, (PermissionDenied, DRFPermissionDenied)):
            return self.error(str(exc) or _("Ruxsat yo‘q."), status=403)
        if isinstance(exc, MethodNotAllowed):
            return self.error(str(exc) or _("Bu metod qo‘llab-quvvatlanmaydi."), status=405)
        if isinstance(exc, (NotAuthenticated, AuthenticationFailed)):
            return self.error(str(exc) or _("Autentifikatsiya talab qilinadi."), status=401)
        if isinstance(exc, Http404):
            return self.error(_("Topilmadi."), status=404)
        if isinstance(exc, Throttled):
            return self.error(_("So'rovlar chegarasi oshdi."), status=429)

        try:
            from src.services.error_reporting.service import ErrorReportingService
            request = self.request
            user = getattr(request, "user", None)
            if user is not None and not user.is_authenticated:
                user = None
            ErrorReportingService.report_error(
                source="BACKEND",
                kind="EXCEPTION",
                severity="ERROR",
                error_type=type(exc).__name__,
                error_message=str(exc),
                stack_trace="".join(
                    traceback.format_exception(type(exc), exc, exc.__traceback__)
                ),
                request_path=request.path,
                request_method=request.method,
                status_code=500,
                user=user,
                context={"api_view": self.__class__.__name__},
            )
        except Exception:
            logger.exception("Failed to report API 500 to ErrorReporting")

        logger.exception("Unhandled API exception", exc_info=exc)
        return self.error(_("Ichki server xatosi."), status=500)

    def dispatch(self, request, *args, **kwargs):
        """Wrap request handling with standard error handling."""
        try:
            return super().dispatch(request, *args, **kwargs)
        except Exception as exc:  # pragma: no cover - covered through callers
            return self.handle_exception(exc)
