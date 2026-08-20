from django.urls import path

from src.frontend.crud.expense.views import (
    ExpenseListView,
    ExpenseCreateView,
    ExpenseDeleteView,
    SalaryListView,
    SalaryCreateView,
    SalaryDeleteView,
    MySalaryListView,
)

urlpatterns = [
    path("expense/list/", ExpenseListView.as_view(), name="expense_list"),
    path("expense/create/", ExpenseCreateView.as_view(), name="expense_create"),
    path("expense/<int:pk>/delete/", ExpenseDeleteView.as_view(), name="expense_delete"),
    path("salary/list/", SalaryListView.as_view(), name="salary_list"),
    path("salary/create/", SalaryCreateView.as_view(), name="salary_create"),
    path("salary/<int:pk>/delete/", SalaryDeleteView.as_view(), name="salary_delete"),
    path("salary/my/", MySalaryListView.as_view(), name="my_salary_list"),
]
