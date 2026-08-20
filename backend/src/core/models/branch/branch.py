from django.utils.translation import gettext_lazy as _

from src.bases.models import *


class Branch(BaseModel):
    name = models.CharField(
        max_length=255,
        verbose_name=_("Nomi"),
        help_text=_("Filial nomi."),
    )
    owner = models.ForeignKey(
        "CustomUser",
        on_delete=models.PROTECT,
        related_name="owned_branches",
        verbose_name=_("Egasi"),
        help_text=_("Filial egasi."),
    )
    address = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name=_("Manzil"),
        help_text=_("Filial manzili."),
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=_("Faol"),
        help_text=_("Filial faollik holati."),
    )

    class Meta:
        db_table = "branches"
        verbose_name = _("Filial")
        verbose_name_plural = _("Filiallar")
        ordering = ["-added_at"]
        indexes = [
            models.Index(fields=["owner"], name="branch_owner_idx"),
            models.Index(fields=["added_at"], name="branch_added_at_idx"),
            models.Index(fields=["is_deleted"], name="branch_is_deleted_idx"),
        ]

    def __str__(self):
        return self.name
