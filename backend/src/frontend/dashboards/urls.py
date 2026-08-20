from django.urls import path

from src.frontend.dashboards.views import (
    AdminDashboardView,
    DashboardRedirectView,
    OwnerBranchListView,
    OwnerBranchEmployeeListView,
    OwnerEmployeeDashboardView,
    PhoneSellerDashboardView,
    AccessorySellerDashboardView,
    CashierDashboardView,
)

urlpatterns = [
    path("dashboard/", DashboardRedirectView.as_view(), name="dashboard"),
    path("admin/dashboard/", AdminDashboardView.as_view(), name="admin-dashboard"),
    path("owner/branches/", OwnerBranchListView.as_view(), name="owner-branches"),
    path(
        "owner/branches/<int:branch_id>/employees/",
        OwnerBranchEmployeeListView.as_view(),
        name="owner-branch-employees",
    ),
    path(
        "owner/branches/<int:branch_id>/employees/<int:employee_id>/dashboard/",
        OwnerEmployeeDashboardView.as_view(),
        name="owner-employee-dashboard",
    ),
    path(
        "seller/phone/dashboard/",
        PhoneSellerDashboardView.as_view(),
        name="seller-dashboard",
    ),
    path(
        "accessory/dashboard/",
        AccessorySellerDashboardView.as_view(),
        name="accessory-seller-dashboard",
    ),
    path(
        "owner/branch/<int:branch_id>/accessory-dashboard/",
        AccessorySellerDashboardView.as_view(),
        name="owner-branch-accessory-dashboard",
    ),
    path("cashier/dashboard/", CashierDashboardView.as_view(), name="cashier-dashboard"),
]
