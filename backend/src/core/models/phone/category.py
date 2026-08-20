from django.utils.translation import gettext_lazy as _

from src.bases.models import *


class PhoneCategory(BaseModel):
    name = models.CharField(
        max_length=255,
        verbose_name=_("Nomi"),
        help_text=_("Telefon kategoriyasi nomi."),
    )
    description = models.TextField(
        null=True,
        blank=True,
        verbose_name=_("Tavsif"),
        help_text=_("Ixtiyoriy kategoriya tavsifi."),
    )

    class Meta:
        db_table = "phone_categories"
        verbose_name = _("Telefon kategoriyasi")
        verbose_name_plural = _("Telefon kategoriyalari")
        ordering = ["name"]
        indexes = [
            models.Index(fields=["is_deleted"], name="phone_category_is_deleted_idx"),
        ]

    def __str__(self):
        return self.name
