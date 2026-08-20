"""Expense API URLs."""

from django.urls import path

from src.api.views.expense import ExpenseCreateAPIView, ExpenseDeleteAPIView, ExpenseListAPIView


class ExpenseListCreateAPIView(ExpenseListAPIView, ExpenseCreateAPIView):
    """List or create expenses with shared API rules."""


urlpatterns = [
    path("expenses/", ExpenseListCreateAPIView.as_view(), name="api_expense_list_create"),
    path("expenses/<int:pk>/", ExpenseDeleteAPIView.as_view(), name="api_expense_delete"),
]
