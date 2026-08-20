from django.urls import path

from src.api.views.dashboard.views import StaffDashboardAPIView

urlpatterns = [
    path("dashboard/staff/", StaffDashboardAPIView.as_view(), name="api_dashboard_staff"),
]
