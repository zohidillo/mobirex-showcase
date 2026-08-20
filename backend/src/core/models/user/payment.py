from django.utils.translation import gettext_lazy as _

from src.bases.models import *


class Payment(BaseModel):
    user = models.ForeignKey(
        "CustomUser",
        on_delete=models.PROTECT,
        related_name="payments",
        verbose_name=_("Foydalanuvchi"),
        help_text=_("To‘lov qaysi foydalanuvchi uchun qo‘shilgan."),
    )
    amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        verbose_name=_("Summa"),
        help_text=_("Qo‘shilgan to‘lov summasi."),
    )
    payment_type = models.CharField(
        max_length=16,
        choices=PAYMENT_TYPE_CHOICES,
        verbose_name=_("To‘lov turi"),
        help_text=_("To‘lov kanali yoki usuli."),
    )
    added_by = models.ForeignKey(
        "CustomUser",
        on_delete=models.PROTECT,
        related_name="added_payments",
        verbose_name=_("Kim qo‘shgan"),
        help_text=_("To‘lovni kiritgan foydalanuvchi."),
    )

    class Meta:
        db_table = "payments"
        verbose_name = _("To‘lov")
        verbose_name_plural = _("To‘lovlar")
        ordering = ["-added_at"]
        indexes = [
            models.Index(fields=["user"], name="payment_user_idx"),
            models.Index(fields=["payment_type"], name="payment_type_idx"),
            models.Index(fields=["added_by"], name="payment_added_by_idx"),
            models.Index(fields=["added_at"], name="payment_added_at_idx"),
            models.Index(fields=["is_deleted"], name="payment_is_deleted_idx"),
        ]

    def __str__(self):
        return f"{self.user.get_username()} - {self.amount}"
