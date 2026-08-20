from django.utils.translation import gettext_lazy as _

from src.bases.models import *


DIRECTION_CHOICES = (
    ("WE_GAVE", _("Biz berdik")),
    ("WE_TOOK", _("Biz oldik")),
)

DOMAIN_CHOICES = (
    ("PHONE", _("Telefon")),
    ("ACCESSORY", _("Aksessuar")),
)


class Debt(BaseModel):
    DOMAIN_PHONE = "PHONE"
    DOMAIN_ACCESSORY = "ACCESSORY"

    branch = models.ForeignKey(
        "core.Branch",
        on_delete=models.PROTECT,
        related_name="debts",
        verbose_name=_("Filial"),
        help_text=_("Qarz tegishli filial."),
    )
    created_by = models.ForeignKey(
        "CustomUser",
        on_delete=models.PROTECT,
        related_name="created_debts",
        verbose_name=_("Yaratuvchi"),
        help_text=_("Qarzni yaratgan foydalanuvchi."),
    )
    phone = models.ForeignKey(
        "core.Phone",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="debts",
        verbose_name=_("Telefon"),
        help_text=_("Ixtiyoriy bog‘langan telefon."),
    )
    f_name = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="Qarz kim bilan bog‘liq (ism familiya)",
    )
    domain = models.CharField(
        max_length=16,
        choices=DOMAIN_CHOICES,
        null=True,
        blank=True,
        verbose_name=_("Yo‘nalish turi"),
        help_text=_("Qarz tegishli savdo yo‘nalishi."),
    )
    amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        verbose_name=_("Qarz summasi"),
        help_text=_("Qarz summasi."),
    )
    remaining_amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        verbose_name=_("Qoldiq"),
        help_text=_("To‘lanmagan qoldiq summa."),
    )
    direction = models.CharField(
        max_length=16,
        choices=DIRECTION_CHOICES,
        verbose_name=_("Yo‘nalish"),
        help_text=_("Qarz yo‘nalishi."),
    )
    note = models.TextField(
        null=True,
        blank=True,
        verbose_name=_("Izoh"),
        help_text=_("Ixtiyoriy izoh."),
    )

    class Meta:
        db_table = "debts"
        verbose_name = _("Qarz")
        verbose_name_plural = _("Qarzlar")
        ordering = ["-added_at"]
        indexes = [
            models.Index(fields=["branch"]),
            models.Index(fields=["created_by"]),
            models.Index(fields=["remaining_amount"]),
            models.Index(fields=["direction"], name="debt_direction_idx"),
            models.Index(fields=["f_name"], name="debt_f_name_idx"),
            models.Index(fields=["domain"], name="debt_domain_idx"),
            models.Index(fields=["added_at"], name="debt_added_at_idx"),
            models.Index(fields=["is_deleted"], name="debt_is_deleted_idx"),
            models.Index(fields=["branch", "added_at"], name="debt_branch_added_at_idx"),
        ]

    def __str__(self):
        return f"{self.amount} - {self.branch}"

    @property
    def remaining(self):
        paid_amount = getattr(self, "paid_amount", None)
        if paid_amount is not None:
            return (self.amount or 0) - (paid_amount or 0)
        return self.remaining_amount or 0
