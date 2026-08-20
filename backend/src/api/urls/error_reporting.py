from django.urls import path

from src.api.views.error_reporting import ErrorReportCreateAPIView

urlpatterns = [
    path(
        "error-report/",
        ErrorReportCreateAPIView.as_view(),
        name="api_error_report_create",
    ),
]
