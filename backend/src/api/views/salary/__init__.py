"""Salary API views."""

from .create import SalaryCreateAPIView
from .delete import SalaryDeleteAPIView
from .list import SalaryAccessMixin, SalaryListAPIView

__all__ = [
    "SalaryAccessMixin",
    "SalaryCreateAPIView",
    "SalaryDeleteAPIView",
    "SalaryListAPIView",
]
