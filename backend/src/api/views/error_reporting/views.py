from drf_spectacular.utils import extend_schema
from rest_framework.permissions import IsAuthenticated
from rest_framework.throttling import ScopedRateThrottle

from src.api.base import BaseAPIView
from src.api.serializers.error_reporting import ErrorReportSerializer
from src.core.models import ErrorReport
from src.services.error_reporting import ErrorReportingService


class ErrorReportCreateAPIView(BaseAPIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "error_report"

    @extend_schema(
        tags=["Error Reporting"],
        request=ErrorReportSerializer,
        responses={201: {"type": "object", "properties": {"received": {"type": "boolean"}}}},
    )
    def post(self, request):
        serializer = ErrorReportSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        platform = (data.get("platform") or "").lower()
        if platform == "android":
            source = ErrorReport.Source.MOBILE_ANDROID
        elif platform == "ios":
            source = ErrorReport.Source.MOBILE_IOS
        else:
            source = ErrorReport.Source.BACKEND

        ErrorReportingService.report_error(
            source=source,
            error_type=data["error_type"],
            error_message=data["error_message"],
            severity=data.get("severity", ErrorReport.Severity.ERROR),
            kind=data.get("kind", ErrorReport.Kind.EXCEPTION),
            stack_trace=data.get("stack_trace"),
            request_path=data.get("request_path"),
            request_method=data.get("request_method"),
            status_code=data.get("status_code"),
            user=request.user,
            app_version=data.get("app_version"),
            platform=data.get("platform"),
            context=data.get("context", {}),
        )
        return self.success({"received": True}, status=201)
