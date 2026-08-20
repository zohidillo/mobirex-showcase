from django.utils.translation import gettext_lazy as _

from src.bases.models import *


class DebtPayment(BaseModel):
    debt = models.ForeignKey(
        "core.Debt",
        on_delete=models.CASCADE,
        related_name="payments",
        verbose_name=_("Qarz"),
        help_text=_("To‘lanayotgan qarz."),
    )
    amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        verbose_name=_("To‘lov summasi"),
        help_text=_("To‘lov summasi."),
    )
    remaining_balance = models.DecimalField(
        max_digits=14,
        verbose_name=_("Qoldiq"),
        decimal_places=2, default=0.00,
        help_text=_("To‘lovdan keyingi qoldiq summa."),
    )
    paid_by = models.ForeignKey(
        "CustomUser",
        on_delete=models.PROTECT,
        related_name="debt_payments",
        verbose_name=_("Kiritgan foydalanuvchi"),
        help_text=_("To‘lovni kiritgan foydalanuvchi."),
    )
    note = models.TextField(
        null=True,
        blank=True,
        verbose_name=_("Izoh"),
        help_text=_("Ixtiyoriy izoh."),
    )

    class Meta:
        db_table = "debt_payments"
        verbose_name = _("Qarz to‘lovi")
        verbose_name_plural = _("Qarz to‘lovlari")
        ordering = ["-added_at"]
        indexes = [
            models.Index(fields=["debt"]),
            models.Index(fields=["paid_by"]),
            models.Index(fields=["added_at"], name="debtpayment_added_at_idx"),
            models.Index(fields=["is_deleted"], name="debtpayment_is_deleted_idx"),
        ]

    def __str__(self):
        return f"{self.amount}"
