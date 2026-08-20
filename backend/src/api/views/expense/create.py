"""Expense create views."""

from drf_spectacular.utils import extend_schema

from src.api.base import BaseAPIView
from src.api.schema import build_success_response_schema
from src.api.serializers.expense import ExpenseCreateSerializer, ExpenseListSerializer
from src.api.views.expense.list import ExpenseAccessMixin


EXPENSE_CREATE_RESPONSE_SCHEMA = build_success_response_schema(
    "ExpenseCreateResponse",
    ExpenseListSerializer,
)


class ExpenseCreateAPIView(ExpenseAccessMixin, BaseAPIView):
    """Create expense. Sellers create for their own branch."""

    @extend_schema(
        tags=["Expense"],
        request=ExpenseCreateSerializer,
        responses={201: EXPENSE_CREATE_RESPONSE_SCHEMA},
    )
    def post(self, request, *args, **kwargs):
        """Create an expense through the existing service."""
        self.require_seller_access(request.user)
        data = request.data.copy()
        data.pop("branch", None)
        data.pop("created_for", None)
        serializer = ExpenseCreateSerializer(data=data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        expense = serializer.save()
        return self.success(
            ExpenseListSerializer(expense, context={"request": request}).data,
            status=201,
        )
