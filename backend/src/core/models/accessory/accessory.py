from django.db.models import Q
from django.utils.translation import gettext_lazy as _

from src.bases.models import *


class Accessory(BaseModel):
    name = models.CharField(
        max_length=255,
        verbose_name=_("Nomi"),
        help_text=_("Aksessuar mahsuloti nomi."),
    )
    category = models.ForeignKey(
        "core.AccessoryCategory",
        on_delete=models.PROTECT,
        related_name="accessories",
        verbose_name=_("Kategoriya"),
        help_text=_("Aksessuar kategoriyasi."),
    )
    branch = models.ForeignKey(
        "core.Branch",
        on_delete=models.PROTECT,
        related_name="accessories",
        verbose_name=_("Filial"),
        help_text=_("Aksessuar tegishli filial."),
    )
    unit_cost = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        verbose_name=_("Birlik tannarxi"),
        help_text=_("Bir dona tannarx."),
    )
    stock = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Soni"),
        help_text=_("Hozirgi qoldiq soni."),
    )
    image = models.ImageField(
        upload_to="accessories/",
        null=True,
        blank=True,
        verbose_name=_("Rasm"),
        help_text=_("Aksessuar rasmi."),
    )
    added_by = models.ForeignKey(
        "CustomUser",
        on_delete=models.PROTECT,
        related_name="added_accessories",
        verbose_name=_("Qo‘shgan foydalanuvchi"),
        help_text=_("Aksessuarni qo‘shgan foydalanuvchi."),
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=_("Faol"),
        help_text=_("Aksessuar faollik holati."),
    )
    is_month_closed = models.BooleanField(
        default=False,
        verbose_name=_("Oy yopilgan"),
        help_text=_("Aksessuar oy yopilishida yopilgan va keyingi oyga ko'chirilgan."),
    )
    month_closed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Oy yopilgan vaqt"),
        help_text=_("Aksessuar oy yopilishida yopilgan vaqt."),
    )
    rolled_over_from = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="rollovers",
        verbose_name=_("Ko'chirilgan manba"),
        help_text=_("Bu aksessuar qaysi eski aksessuurdan ko'chirilganligi."),
    )

    class Meta:
        db_table = "accessories"
        verbose_name = _("Aksessuar")
        verbose_name_plural = _("Aksessuarlar")
        ordering = ["-added_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["branch", "name", "unit_cost"],
                condition=Q(is_month_closed=False, is_deleted=False),
                name="unique_active_accessory_branch_name_cost",
            )
        ]
        indexes = [
            models.Index(fields=["branch"], name="accessory_branch_idx"),
            models.Index(fields=["category"], name="accessory_category_idx"),
            models.Index(fields=["added_at"], name="accessory_added_at_idx"),
            models.Index(fields=["is_deleted"], name="accessory_is_deleted_idx"),
            models.Index(fields=["branch", "is_month_closed"], name="acc_branch_closed_idx"),
        ]

    def __str__(self):
        return f"{self.name} - {self.unit_cost}"
