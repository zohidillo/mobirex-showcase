from django.utils.translation import gettext_lazy as _

from src.bases.models import *


class AccessorySale(BaseModel):
    accessory = models.ForeignKey(
        "core.Accessory",
        on_delete=models.PROTECT,
        related_name="sales",
        verbose_name=_("Aksessuar"),
        help_text=_("Sotilayotgan aksessuar."),
    )
    branch = models.ForeignKey(
        "core.Branch",
        on_delete=models.PROTECT,
        related_name="accessory_sales",
        verbose_name=_("Filial"),
        help_text=_("Savdo bo‘lib o‘tgan filial."),
    )
    quantity = models.PositiveIntegerField(
        verbose_name=_("Soni"),
        help_text=_("Sotilgan soni."),
    )
    unit_cost = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        verbose_name=_("Birlik tannarxi"),
        help_text=_("Savdo paytidagi birlik tannarx (snapshot)."),
    )
    total_cost = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        verbose_name=_("Jami tannarx"),
        help_text=_("Jami tannarx = soni × birlik tannarx."),
    )
    total_price = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        verbose_name=_("Jami sotuv narxi"),
        help_text=_("Sotuvchi kiritgan jami sotuv narxi."),
    )
    profit = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        verbose_name=_("Foyda"),
        help_text=_("Foyda = jami sotuv − jami tannarx."),
    )
    sold_by = models.ForeignKey(
        "CustomUser",
        on_delete=models.PROTECT,
        related_name="accessory_sales",
        verbose_name=_("Sotgan foydalanuvchi"),
        help_text=_("Aksessuarni sotgan foydalanuvchi."),
    )
    sold_at = models.DateTimeField(
        verbose_name=_("Sotilgan vaqt"),
        help_text=_("Savdo sanasi/vaqti."),
    )

    class Meta:
        db_table = "accessory_sales"
        verbose_name = _("Aksessuar savdosi")
        verbose_name_plural = _("Aksessuar savdolari")
        ordering = ["-sold_at", "-added_at"]
        indexes = [
            models.Index(fields=["branch"]),
            models.Index(fields=["sold_at"]),
            models.Index(fields=["is_deleted"], name="accessorysale_is_deleted_idx"),
        ]

    def __str__(self):
        return f"{self.accessory.name} - {self.total_price}"
