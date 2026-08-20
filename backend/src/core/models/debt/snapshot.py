from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from src.bases.models import *
from .debt import DIRECTION_CHOICES


class DebtMonthlySnapshot(models.Model):
    debt = models.ForeignKey(
        "core.Debt",
        on_delete=models.PROTECT,
        related_name="monthly_snapshots",
        verbose_name=_("Qarz"),
        help_text=_("Snapshot tegishli qarz."),
    )
    branch = models.ForeignKey(
        "core.Branch",
        on_delete=models.PROTECT,
        related_name="debt_monthly_snapshots",
        verbose_name=_("Filial"),
        help_text=_("Snapshot tegishli filial."),
    )
    month = models.DateField(
        verbose_name=_("Oy"),
        help_text=_("Snapshot oyi (oyning birinchi kuni)."),
    )
    remaining_amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        verbose_name=_("Qoldiq"),
        help_text=_("Tanlangan oy oxiridagi qoldiq summa."),
    )
    total_paid_until_month = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        verbose_name=_("Shu oygacha to‘langan"),
        help_text=_("Tanlangan oy oxirigacha jami to‘langan summa."),
    )
    direction = models.CharField(
        max_length=16,
        choices=DIRECTION_CHOICES,
        verbose_name=_("Yo‘nalish"),
        help_text=_("Qarz yo‘nalishi snapshotdagi holatda."),
    )
    f_name = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text=_("Qarz kim bilan bog‘liq (ism familiya)."),
    )
    note = models.TextField(
        null=True,
        blank=True,
        verbose_name=_("Izoh"),
        help_text=_("Snapshotdagi izoh nusxasi."),
    )
    created_by = models.ForeignKey(
        "CustomUser",
        on_delete=models.PROTECT,
        related_name="debt_monthly_snapshots",
        verbose_name=_("Kiritgan"),
        help_text=_("Qarzni kiritgan foydalanuvchi nusxasi."),
    )
    original_created_at = models.DateTimeField(
        verbose_name=_("Asl yaratilgan vaqt"),
        help_text=_("Asl qarz yaratilgan vaqt."),
    )
    snapshot_created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Snapshot yaratilgan vaqt"),
        help_text=_("Snapshot yozuvi yaratilgan vaqt."),
    )

    class Meta:
        db_table = "debt_monthly_snapshots"
        verbose_name = _("Qarz oylik snapshoti")
        verbose_name_plural = _("Qarz oylik snapshotlari")
        ordering = ["-month", "-snapshot_created_at", "-id"]
        constraints = [
            models.UniqueConstraint(
                fields=["debt", "month"],
                name="unique_debt_month_snapshot",
            ),
        ]
        indexes = [
            models.Index(fields=["month"], name="debt_snap_month_idx"),
            models.Index(fields=["branch", "month"], name="debt_snap_branch_month_idx"),
            models.Index(fields=["created_by", "month"], name="debt_snap_creator_month_idx"),
        ]

    def clean(self):
        if self.month and self.month.day != 1:
            raise ValidationError({"month": _("Oy qiymati oyning birinchi kuni bo‘lishi kerak.")})

    def save(self, *args, **kwargs):
        if self.pk:
            raise ValidationError(_("Snapshot yozuvini yangilash mumkin emas."))
        self.full_clean()
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError(_("Snapshot yozuvini o‘chirish mumkin emas."))

    def __str__(self):
        return f"{self.debt_id} - {self.month} - {self.remaining_amount}"
