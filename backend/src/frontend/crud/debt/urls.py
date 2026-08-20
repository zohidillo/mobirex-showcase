from django.urls import path

from src.frontend.crud.debt.views import (
    DebtListView,
    PaidDebtsListView,
    DebtCreateView,
    DebtDeleteView,
    DebtPaymentListView,
    DebtPaymentCreateView,
    DebtPaymentDebtOptionsView,
    DebtPaymentDeleteView,
)

urlpatterns = [
    path("debt/list/", DebtListView.as_view(), name="debt_list"),
    path("debt/paid/", PaidDebtsListView.as_view(), name="debt_paid_list"),
    path("debt/create/", DebtCreateView.as_view(), name="debt_create"),
    path("debt/<int:pk>/delete/", DebtDeleteView.as_view(), name="debt_delete"),
    path("debt/payment/list/", DebtPaymentListView.as_view(), name="debt_payment_list"),
    path("debt/payment/create/", DebtPaymentCreateView.as_view(), name="debt_payment_create"),
    path(
        "debt/payment/debts/",
        DebtPaymentDebtOptionsView.as_view(),
        name="debt_payment_debt_options",
    ),
    path(
        "debt/payment/<int:pk>/delete/",
        DebtPaymentDeleteView.as_view(),
        name="debt_payment_delete",
    ),
]
