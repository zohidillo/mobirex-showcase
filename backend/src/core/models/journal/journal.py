from django.utils.translation import gettext_lazy as _

from src.bases.models import *


ACTION_CHOICES = (
    ("CREATE", _("Yaratish")),
    ("UPDATE", _("Yangilash")),
    ("DELETE", _("O‘chirish")),
)


class Journal(BaseModel):
    branch = models.ForeignKey(
        "core.Branch",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="journals",
        verbose_name=_("Filial"),
        help_text=_("Jurnal yozuvi tegishli filial."),
    )
    user = models.ForeignKey(
        "CustomUser",
        on_delete=models.PROTECT,
        related_name="journals",
        verbose_name=_("Foydalanuvchi"),
        help_text=_("Amalni bajargan foydalanuvchi."),
    )
    action = models.CharField(
        max_length=16,
        choices=ACTION_CHOICES,
        verbose_name=_("Amal"),
        help_text=_("Amal turi."),
    )
    model_name = models.CharField(
        max_length=255,
        verbose_name=_("Model nomi"),
        help_text=_("O‘zgartirilgan model."),
    )
    object_id = models.IntegerField(
        verbose_name=_("Obyekt ID"),
        help_text=_("O‘zgartirilgan obyekt ID si."),
    )
    object_repr = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name=_("Obyekt ko‘rinishi"),
        help_text=_("Obyektning o‘qiladigan ko‘rinishi."),
    )
    old_data = models.JSONField(
        null=True,
        blank=True,
        verbose_name=_("Oldingi ma’lumotlar"),
        help_text=_("Oldingi ma’lumotlar snapshoti."),
    )
    new_data = models.JSONField(
        null=True,
        blank=True,
        verbose_name=_("Yangi ma’lumotlar"),
        help_text=_("Yangi ma’lumotlar snapshoti."),
    )

    class Meta:
        db_table = "journals"
        verbose_name = _("Jurnal")
        verbose_name_plural = _("Jurnallar")
        ordering = ["-added_at"]
        indexes = [
            models.Index(fields=["branch"]),
            models.Index(fields=["user"]),
            models.Index(fields=["model_name"]),
            models.Index(fields=["action"], name="journal_action_idx"),
            models.Index(fields=["added_at"], name="journal_added_at_idx"),
        ]

    def __str__(self):
        return f"{self.model_name} - {self.action}"
