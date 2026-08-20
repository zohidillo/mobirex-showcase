"""Debt payment views."""

from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _

from drf_spectacular.utils import extend_schema

import src.core.models as models
from src.api.base import BaseAPIView
from src.api.schema import build_success_response_schema
from src.api.serializers.debt import DebtPaySerializer, DebtPaymentSerializer
from src.api.views.debt.list import DebtAccessMixin
from src.services.debt import DebtPaymentCreateService, is_debt_in_current_month


DEBT_PAY_RESPONSE_SCHEMA = build_success_response_schema(
    "DebtPayResponse",
    DebtPaymentSerializer,
)


class DebtPayAPIView(DebtAccessMixin, BaseAPIView):
    """Pay debt. Uses original debt capital routing through the service."""

    def get_object(self):
        """Return the target open debt when the user has access."""
        debt = get_object_or_404(
            models.Debt.objects.select_related("branch", "created_by"),
            pk=self.kwargs["pk"],
            is_deleted=False,
            remaining_amount__gt=0,
        )
        user = self.request.user
        self.require_view_access(user)

        if not self.can_view_or_pay_debt(user, debt):
            raise PermissionDenied(_("Sizga bu amalni bajarish mumkin emas."))

        if not is_debt_in_current_month(debt):
            raise PermissionDenied(_("Faqat joriy oy qarziga to‘lov qilish mumkin."))
        return debt

    @extend_schema(
        tags=["Debt"],
        request=DebtPaySerializer,
        responses={200: DEBT_PAY_RESPONSE_SCHEMA},
    )
    def post(self, request, *args, **kwargs):
        """Create a debt payment by delegating to the existing service."""
        debt = self.get_object()
        serializer = DebtPaySerializer(data=request.data, context={"request": request, "debt": debt})
        serializer.is_valid(raise_exception=True)
        payment = DebtPaymentCreateService.create_payment(
            debt=debt,
            amount=serializer.validated_data["amount"],
            paid_by=request.user,
            note=serializer.validated_data.get("note"),
        )
        return self.success(
            DebtPaymentSerializer(payment, context={"request": request}).data,
            status=200,
        )
