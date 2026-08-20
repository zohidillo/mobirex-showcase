from django.urls import path

from src.frontend.cashier.views import (
    CashierDashboardView,
    PaymentCreateView,
    PaymentListView,
    TransactionLogListView,
    LegacyPaymentMutationView,
)

urlpatterns = [
    path("cashier/dashboard/", CashierDashboardView.as_view(), name="cashier_dashboard"),
    path("cashier/payments/", PaymentListView.as_view(), name="cashier_payment_list"),
    path(
        "cashier/payments/create/",
        PaymentCreateView.as_view(),
        name="cashier_payment_create",
    ),
    path(
        "cashier/payments/<int:pk>/update/",
        LegacyPaymentMutationView.as_view(),
        name="cashier_payment_update",
    ),
    path(
        "cashier/payments/<int:pk>/delete/",
        LegacyPaymentMutationView.as_view(),
        name="cashier_payment_delete",
    ),
    path(
        "cashier/transactions/",
        TransactionLogListView.as_view(),
        name="cashier_transaction_list",
    ),
]
