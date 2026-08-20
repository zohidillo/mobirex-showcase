"""Salary API URLs."""

from django.urls import path

from src.api.views.salary import SalaryCreateAPIView, SalaryDeleteAPIView, SalaryListAPIView


class SalaryListCreateAPIView(SalaryListAPIView, SalaryCreateAPIView):
    """List or create salaries with shared API rules."""


urlpatterns = [
    path("salary/", SalaryListCreateAPIView.as_view(), name="api_salary_list_create"),
    path("salary/<int:pk>/", SalaryDeleteAPIView.as_view(), name="api_salary_delete"),
]
