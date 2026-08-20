from django.db.models import Q
from django.utils.translation import gettext_lazy as _

from src.bases.models import *


class TransactionLog(BaseModel):
    user = models.ForeignKey(
        "CustomUser",
        on_delete=models.PROTECT,
        related_name="transaction_logs",
        verbose_name=_("Foydalanuvchi"),
        help_text=_("Tranzaksiya tegishli foydalanuvchi."),
    )
    type = models.CharField(
        max_length=32,
        choices=TRANSACTION_TYPE_CHOICES,
        verbose_name=_("Turi"),
        help_text=_("Tranzaksiya turi."),
    )
    amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        verbose_name=_("Summa"),
        help_text=_("Tranzaksiya summasi."),
    )
    charge_date = models.DateTimeField(
        default=timezone.now,
        verbose_name=_("Sana"),
        help_text=_("Amal bajarilgan sana va vaqt."),
    )
    charge_day = models.DateField(
        null=True,
        blank=True,
        editable=False,
        verbose_name=_("Hisoblangan kun"),
        help_text=_("Kunlik yechimlar uchun texnik sana maydoni."),
    )
    balance_before = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        verbose_name=_("Oldingi balans"),
        help_text=_("Amaldan oldingi balans."),
    )
    balance_after = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        verbose_name=_("Keyingi balans"),
        help_text=_("Amaldan keyingi balans."),
    )

    class Meta:
        db_table = "transaction_logs"
        verbose_name = _("Tranzaksiya jurnali")
        verbose_name_plural = _("Tranzaksiya jurnallari")
        ordering = ["-charge_date", "-id"]
        indexes = [
            models.Index(fields=["user"], name="txnlog_user_idx"),
            models.Index(fields=["type"], name="txnlog_type_idx"),
            models.Index(fields=["charge_date"], name="txnlog_charge_date_idx"),
            models.Index(fields=["charge_day"], name="txnlog_charge_day_idx"),
            models.Index(fields=["added_at"], name="txnlog_added_at_idx"),
            models.Index(fields=["is_deleted"], name="txnlog_is_deleted_idx"),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "charge_day", "type"],
                condition=Q(type="daily_charge", is_deleted=False),
                name="uniq_daily_charge_per_user_day",
            ),
        ]

    def save(self, *args, **kwargs):
        if self.charge_date:
            self.charge_day = timezone.localdate(self.charge_date)
        else:
            self.charge_day = timezone.localdate()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.get_username()} - {self.type} - {self.amount}"
