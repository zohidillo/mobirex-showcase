"""Owner mobile helper API URLs."""

from django.urls import path

from src.api.views.me import OwnerBranchListAPIView, OwnerStaffListAPIView


urlpatterns = [
    path("me/branches/", OwnerBranchListAPIView.as_view(), name="api_me_branches"),
    path("me/staff/", OwnerStaffListAPIView.as_view(), name="api_me_staff"),
]
