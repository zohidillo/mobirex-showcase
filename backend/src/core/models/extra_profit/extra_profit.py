from django.utils.translation import gettext_lazy as _

from src.bases.models import *


class ExtraProfit(BaseModel):
    branch = models.ForeignKey(
        "core.Branch",
        on_delete=models.PROTECT,
        related_name="extra_profits",
        verbose_name=_("Filial"),
        help_text=_("Qo‘shimcha foyda olgan filial."),
    )
    created_by = models.ForeignKey(
        "CustomUser",
        on_delete=models.PROTECT,
        related_name="created_extra_profits",
        verbose_name=_("Yaratuvchi"),
        help_text=_("Qo‘shimcha foydani kiritgan foydalanuvchi."),
    )
    amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        verbose_name=_("Foyda summasi"),
        help_text=_("Qo‘shimcha foyda summasi."),
    )
    note = models.TextField(
        null=True,
        blank=True,
        verbose_name=_("Izoh"),
        help_text=_("Foyda manbasi bo‘yicha ixtiyoriy izoh."),
    )

    class Meta:
        db_table = "extra_profits"
        verbose_name = _("Qo‘shimcha foyda")
        verbose_name_plural = _("Qo‘shimcha foydalar")
        ordering = ["-added_at"]
        indexes = [
            models.Index(fields=["branch"]),
            models.Index(fields=["created_by"], name="extra_profit_created_by_idx"),
            models.Index(fields=["added_at"], name="extra_profit_added_at_idx"),
            models.Index(fields=["is_deleted"], name="extra_profit_is_deleted_idx"),
            models.Index(fields=["branch", "added_at"], name="extra_profit_branch_add_idx"),
        ]

    def __str__(self):
        return f"{self.branch} - {self.amount}"
