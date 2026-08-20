from django.utils.translation import gettext_lazy as _

from src.bases.models import *


class MonthClosingRecord(BaseModel):
    STATUS_STARTED = "started"
    STATUS_COMPLETED = "completed"
    STATUS_FAILED = "failed"

    STATUS_CHOICES = (
        (STATUS_STARTED, _("Boshlangan")),
        (STATUS_COMPLETED, _("Yakunlangan")),
        (STATUS_FAILED, _("Muvaffaqiyatsiz")),
    )

    branch = models.ForeignKey(
        "core.Branch",
        on_delete=models.PROTECT,
        related_name="month_closings",
        verbose_name=_("Filial"),
        help_text=_("Oy yopilgan filial."),
    )
    month = models.DateField(
        verbose_name=_("Oy"),
        help_text=_("Yopilgan oy (oyning birinchi kuni)."),
    )
    status = models.CharField(
        max_length=16,
        choices=STATUS_CHOICES,
        default=STATUS_COMPLETED,
        verbose_name=_("Holat"),
        help_text=_("Oy yopilish jarayonining holati."),
    )
    started_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Boshlangan vaqt"),
        help_text=_("Oy yopilish jarayoni boshlangan vaqt."),
    )
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Yakunlangan vaqt"),
        help_text=_("Oy yopilish jarayoni yakunlangan vaqt."),
    )
    phones_closed = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Yopilgan telefonlar"),
        help_text=_("Oy yopilishida yopilgan telefonlar soni."),
    )
    phones_recreated = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Qayta yaratilgan telefonlar"),
        help_text=_("Keyingi oy uchun qayta yaratilgan telefonlar soni."),
    )
    accessories_processed = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Qayta hisoblangan aksessuarlar"),
        help_text=_("Oy yopilishida qayta hisoblangan aksessuarlar soni."),
    )
    debt_adjustment_applied = models.BooleanField(
        default=False,
        verbose_name=_("Qarz tuzatmasi qo’llangan"),
        help_text=_("Snapshotdan capitalga qarz tuzatmasi qo’llanganligini bildiradi."),
    )
    debt_adjustment_amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0,
        verbose_name=_("Qarz tuzatmasi summasi"),
        help_text=_("Oy yopilishida capitalga qo’llangan jami qarz tuzatmasi."),
    )
    accessories_recreated = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Qayta yaratilgan aksessuarlar"),
        help_text=_("Keyingi oy uchun qayta yaratilgan aksessuar qatorlari soni."),
    )
    phone_rollover_applied = models.BooleanField(
        default=False,
        verbose_name=_("Telefon rollover qo’llangan"),
        help_text=_("Telefon rollover kapital ta’siri qo’llanganligini bildiradi."),
    )
    phone_rollover_amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0,
        verbose_name=_("Telefon rollover summasi"),
        help_text=_("Keyingi oy PhoneCapital.current_balance’dan ayirilgan jami summa."),
    )
    accessory_rollover_applied = models.BooleanField(
        default=False,
        verbose_name=_("Aksessuar rollover qo’llangan"),
        help_text=_("Aksessuar rollover kapital ta’siri qo’llanganligini bildiradi."),
    )
    accessory_rollover_amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0,
        verbose_name=_("Aksessuar rollover summasi"),
        help_text=_("Keyingi oy AccessoryCapital.invested_amount’ga qo’shilgan jami summa."),
    )

    class Meta:
        db_table = "month_closing_records"
        verbose_name = _("Oy yopilishi")
        verbose_name_plural = _("Oy yopilishlari")
        ordering = ["-month", "-added_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["branch", "month"],
                name="unique_branch_month_closing",
            ),
        ]
        indexes = [
            models.Index(fields=["branch", "month"], name="month_close_branch_month_idx"),
            models.Index(fields=["is_deleted"], name="month_close_is_deleted_idx"),
        ]

    def __str__(self):
        return f"{self.branch} - {self.month}"
