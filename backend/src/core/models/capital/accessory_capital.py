from django.utils.translation import gettext_lazy as _

from src.bases.models import *


class AccessoryCapital(BaseModel):
    branch = models.ForeignKey(
        "core.Branch",
        on_delete=models.PROTECT,
        related_name="accessory_capitals",
        verbose_name=_("Filial"),
        help_text=_("Kapital tegishli filial."),
    )
    month = models.DateField(
        verbose_name=_("Oy"),
        help_text=_("Kapital oyi (oyning birinchi kuni)."),
    )
    invested_amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0,
        verbose_name=_("Tikilgan pul"),
        help_text=_("Ushbu oy uchun aksessuar kapitaliga tikilgan pul."),
    )
    current_balance = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0,
        verbose_name=_("Hozirgi balans"),
        help_text=_("Aksessuar kapitalining hozirgi balansi."),
    )
    debt_adjustment = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0,
        verbose_name=_("Qarz tuzatmasi"),
        help_text=_("Snapshot asosida qo‘llangan qarz tuzatmasi."),
    )

    class Meta:
        db_table = "accessory_capitals"
        verbose_name = _("Aksessuar kapitali")
        verbose_name_plural = _("Aksessuar kapitallari")
        ordering = ["-month", "-added_at"]
        unique_together = ["branch", "month"]
        indexes = [
            models.Index(fields=["branch", "month"], name="acc_cap_branch_month_idx"),
            models.Index(fields=["is_deleted"], name="acc_cap_is_del_idx"),
        ]

    def __str__(self):
        return f"{self.branch} - {self.month}"

    @property
    def balance(self):
        return self.current_balance or 0
