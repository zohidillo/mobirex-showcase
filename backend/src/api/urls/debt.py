"""Debt API URLs."""

from django.urls import path

from src.api.views.debt import (
    ClosedDebtListAPIView,
    DebtCreateAPIView,
    DebtDeleteAPIView,
    DebtListAPIView,
    DebtPayAPIView,
    DebtPaymentDeleteAPIView,
    DebtPaymentListAPIView,
)


class DebtListCreateAPIView(DebtListAPIView, DebtCreateAPIView):
    """List or create debts with shared API rules."""


urlpatterns = [
    path("debts/", DebtListCreateAPIView.as_view(), name="api_debt_list_create"),
    path("debts/closed/", ClosedDebtListAPIView.as_view(), name="api_debt_closed_list"),
    path("debts/<int:pk>/pay/", DebtPayAPIView.as_view(), name="api_debt_pay"),
    path("debts/payments/", DebtPaymentListAPIView.as_view(), name="api_debt_payment_list"),
    path(
        "debts/payments/<int:pk>/",
        DebtPaymentDeleteAPIView.as_view(),
        name="api_debt_payment_delete",
    ),
    path("debts/<int:pk>/", DebtDeleteAPIView.as_view(), name="api_debt_delete"),
]
