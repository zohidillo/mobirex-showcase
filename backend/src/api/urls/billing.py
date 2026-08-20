"""Billing API URLs."""

from django.urls import path

from src.api.views.billing import (
    BillingPaymentCreateAPIView,
    BillingPaymentListAPIView,
    TransactionLogListAPIView,
)


class BillingPaymentListCreateAPIView(BillingPaymentListAPIView, BillingPaymentCreateAPIView):
    """List or create billing payments with cashier rules."""


urlpatterns = [
    path(
        "billing/payments/",
        BillingPaymentListCreateAPIView.as_view(),
        name="api_billing_payment_list_create",
    ),
    path(
        "billing/transactions/",
        TransactionLogListAPIView.as_view(),
        name="api_billing_transaction_list",
    ),
]
