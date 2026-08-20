from .admin_dashboard import AdminDashboardView
from .owner_dashboard import (
    OwnerBranchListView,
    OwnerBranchEmployeeListView,
    OwnerEmployeeDashboardView,
)
from .phone_seller_dashboard import PhoneSellerDashboardView
from .accessory_seller_dashboard import AccessorySellerDashboardView
from .cashier_dashboard import CashierDashboardView
from .dashboard_redirect import DashboardRedirectView

__all__ = [
    "AdminDashboardView",
    "OwnerBranchListView",
    "OwnerBranchEmployeeListView",
    "OwnerEmployeeDashboardView",
    "PhoneSellerDashboardView",
    "AccessorySellerDashboardView",
    "CashierDashboardView",
    "DashboardRedirectView",
]
