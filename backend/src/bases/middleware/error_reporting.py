import logging
import traceback

from django.core.exceptions import PermissionDenied as DjangoPermissionDenied
from django.core.exceptions import ValidationError as DjangoValidationError
from django.http import Http404

from src.services.error_reporting.service import ErrorReportingService

logger = logging.getLogger(__name__)

_USER_ERROR_TYPES = (
    DjangoValidationError,
    DjangoPermissionDenied,
    Http404,
)


class ErrorReportingMiddleware:
    """
    Catches uncaught exceptions from web views and non-DRF middleware via
    process_exception and forwards them to ErrorReportingService.

    DRF views never reach process_exception because DRF catches exceptions
    internally inside dispatch(). Those are handled in BaseAPIView.handle_exception.

    This middleware never modifies the response — Django shows its default
    500 page as usual.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_exception(self, request, exception):
        if isinstance(exception, _USER_ERROR_TYPES):
            return None

        try:
            user = getattr(request, "user", None)
            if user is not None and not user.is_authenticated:
                user = None

            ErrorReportingService.report_error(
                source="BACKEND",
                kind="EXCEPTION",
                severity="ERROR",
                error_type=type(exception).__name__,
                error_message=str(exception),
                stack_trace="".join(
                    traceback.format_exception(
                        type(exception), exception, exception.__traceback__
                    )
                ),
                request_path=request.path,
                request_method=request.method,
                user=user,
                context={
                    "middleware": True,
                    "is_api": request.path.startswith("/api/"),
                },
            )
        except Exception:
            logger.exception("ErrorReportingMiddleware.process_exception failed")

        return None
