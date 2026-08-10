"""Custom DRF exception handler — tracks repeated validation errors per user."""

import logging

from rest_framework.exceptions import ValidationError as DRFValidationError
from rest_framework.views import exception_handler as drf_exception_handler

from src.services.error_reporting.service import ErrorReportingService

logger = logging.getLogger(__name__)


def api_exception_handler(exc, context):
    response = drf_exception_handler(exc, context)

    try:
        request = context.get("request")
        if (
            isinstance(exc, DRFValidationError)
            and request is not None
            and getattr(request, "user", None) is not None
            and request.user.is_authenticated
        ):
            ErrorReportingService.track_user_validation_error(
                user=request.user,
                error_type=type(exc).__name__,
                request_path=request.path,
                error_message=str(exc),
            )
    except Exception:
        logger.exception("Validation tracking failed in api_exception_handler")

    return response
