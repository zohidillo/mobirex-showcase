"""Salary create views."""

from drf_spectacular.utils import extend_schema

from src.api.base import BaseAPIView
from src.api.schema import build_success_response_schema
from src.api.serializers.salary import SalaryCreateSerializer, SalaryListSerializer
from src.api.views.salary.list import SalaryAccessMixin


SALARY_CREATE_RESPONSE_SCHEMA = build_success_response_schema(
    "SalaryCreateResponse",
    SalaryListSerializer,
)


class SalaryCreateAPIView(SalaryAccessMixin, BaseAPIView):
    """Create salary. Only owners are allowed."""

    @extend_schema(
        tags=["Salary"],
        request=SalaryCreateSerializer,
        responses={201: SALARY_CREATE_RESPONSE_SCHEMA},
    )
    def post(self, request, *args, **kwargs):
        """Create a salary through the existing service."""
        serializer = SalaryCreateSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        salary = serializer.save()
        return self.success(
            SalaryListSerializer(salary, context={"request": request}).data,
            status=201,
        )
