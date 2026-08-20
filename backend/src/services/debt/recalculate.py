from decimal import Decimal

from django.db import transaction

from src.core.models import Debt, DebtPayment


class RecalculateDebtService:
    @staticmethod
    def recalculate(debt):
        with transaction.atomic():
            locked_debt = Debt.objects.select_for_update().get(pk=debt.pk)
            payments = list(
                DebtPayment.objects.select_for_update()
                .filter(debt=locked_debt, is_deleted=False)
                .only("id", "amount", "remaining_balance")
                .order_by("added_at", "id")
            )

            running_remaining = locked_debt.amount or Decimal("0.00")
            changed_payments = []

            for payment in payments:
                running_remaining = running_remaining - (payment.amount or Decimal("0.00"))
                payment_remaining = max(running_remaining, Decimal("0.00"))
                if payment.remaining_balance != payment_remaining:
                    payment.remaining_balance = payment_remaining
                    changed_payments.append(payment)

            if changed_payments:
                DebtPayment.all_objects.bulk_update(changed_payments, ["remaining_balance"])

            debt_remaining = max(running_remaining, Decimal("0.00"))
            if locked_debt.remaining_amount != debt_remaining:
                locked_debt.remaining_amount = debt_remaining
                locked_debt.save(update_fields=["remaining_amount", "updated_at"])

            return locked_debt
