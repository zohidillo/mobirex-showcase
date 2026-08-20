from django.utils.translation import gettext_lazy as _

from src.bases.models import *


class SubscriptionPayment(BaseModel):
    user = models.ForeignKey(
        "CustomUser",
        on_delete=models.PROTECT,
        related_name="subscription_payments",
        verbose_name=_("Foydalanuvchi"),
        help_text=_("Obuna uchun to‘lov qilgan foydalanuvchi."),
    )
    subscription = models.ForeignKey(
        "core.Subscription",
        on_delete=models.CASCADE,
        related_name="payments",
        verbose_name=_("Obuna"),
        help_text=_("Bog‘langan obuna."),
    )
    amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        verbose_name=_("To‘lov summasi"),
        help_text=_("To‘lov summasi."),
    )
    period_type = models.CharField(
        max_length=16,
        choices=SUB_PERIOD_CHOICES,
        verbose_name=_("Davr turi"),
        help_text=_("To‘lov davr turi."),
    )
    paid_at = models.DateTimeField(
        default=timezone.now,
        verbose_name=_("To‘lov vaqti"),
        help_text=_("To‘lov sanasi/vaqti."),
    )
    added_by = models.ForeignKey(
        "CustomUser",
        on_delete=models.PROTECT,
        related_name="added_subscription_payments",
        verbose_name=_("Kiritgan foydalanuvchi"),
        help_text=_("To‘lovni kim kiritgan (kassir/egasi/admin)."),
    )
    note = models.TextField(
        null=True,
        blank=True,
        verbose_name=_("Izoh"),
        help_text=_("Ixtiyoriy izoh."),
    )

    class Meta:
        db_table = "subscription_payments"
        verbose_name = _("Obuna to‘lovi")
        verbose_name_plural = _("Obuna to‘lovlari")
        ordering = ["-added_at"]
        indexes = [
            models.Index(fields=["user"], name="subpay_user_idx"),
            models.Index(fields=["subscription"], name="subpay_subscription_idx"),
            models.Index(fields=["paid_at"], name="subpay_paid_at_idx"),
            models.Index(fields=["added_at"], name="subpay_added_at_idx"),
            models.Index(fields=["added_by"], name="subpay_added_by_idx"),
            models.Index(fields=["is_deleted"], name="subpay_is_deleted_idx"),
        ]

    def __str__(self):
        return f"{self.user.get_username()} - {self.amount} - {self.paid_at}"
