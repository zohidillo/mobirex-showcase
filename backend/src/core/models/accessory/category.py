from django.utils.translation import gettext_lazy as _

from src.bases.models import *


class AccessoryCategory(BaseModel):
    name = models.CharField(
        max_length=255,
        verbose_name=_("Nomi"),
        help_text=_("Aksessuar kategoriyasi nomi."),
    )
    description = models.TextField(
        null=True,
        blank=True,
        verbose_name=_("Tavsif"),
        help_text=_("Ixtiyoriy kategoriya tavsifi."),
    )

    class Meta:
        db_table = "accessory_categories"
        verbose_name = _("Aksessuar kategoriyasi")
        verbose_name_plural = _("Aksessuar kategoriyalari")
        ordering = ["name"]
        indexes = [
            models.Index(fields=["is_deleted"], name="acc_cat_is_del_idx"),
        ]

    def __str__(self):
        return self.name
