from django.utils.translation import gettext_lazy as _

from src.bases.models import *


EXPENSE_TYPE_CHOICES = (
    ("SHOP_EXPENSE", _("Do‘kon xarajati")),
    ("EMPLOYEE_EXPENSE", _("Xodim xarajati")),
)

EXPENSE_CAPITAL_TYPE_CHOICES = (
    ("phone", _("Telefon kapitali")),
    ("accessory", _("Aksessuar kapitali")),
)


class Expense(BaseModel):
    CAPITAL_TYPE_PHONE = "phone"
    CAPITAL_TYPE_ACCESSORY = "accessory"

    branch = models.ForeignKey(
        "core.Branch",
        on_delete=models.PROTECT,
        related_name="expenses",
        verbose_name=_("Filial"),
        help_text=_("Xarajat tegishli filial."),
    )
    created_by = models.ForeignKey(
        "CustomUser",
        on_delete=models.PROTECT,
        related_name="created_expenses",
        verbose_name=_("Yaratuvchi"),
        help_text=_("Xarajatni yaratgan foydalanuvchi."),
    )
    type = models.CharField(
        max_length=32,
        choices=EXPENSE_TYPE_CHOICES,
        verbose_name=_("Xarajat turi"),
        help_text=_("Xarajat turi."),
    )
    amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        verbose_name=_("Xarajat summasi"),
        help_text=_("Xarajat summasi."),
    )
    capital_type = models.CharField(
        max_length=16,
        choices=EXPENSE_CAPITAL_TYPE_CHOICES,
        null=True,
        blank=True,
        verbose_name=_("Kapital turi"),
        help_text=_("Xarajat ta’sir qilgan kapital turi."),
    )
    note = models.TextField(
        null=True,
        blank=True,
        verbose_name=_("Izoh"),
        help_text=_("Ixtiyoriy izoh."),
    )

    class Meta:
        db_table = "expenses"
        verbose_name = _("Xarajat")
        verbose_name_plural = _("Xarajatlar")
        ordering = ["-added_at"]
        indexes = [
            models.Index(fields=["branch"]),
            models.Index(fields=["created_by"]),
            models.Index(fields=["type"], name="expense_type_idx"),
            models.Index(fields=["added_at"], name="expense_added_at_idx"),
            models.Index(fields=["is_deleted"], name="expense_is_deleted_idx"),
            models.Index(fields=["branch", "added_at"], name="expense_branch_added_at_idx"),
        ]

    def __str__(self):
        return f"{self.amount}"

    @property
    def amount_safe(self):
        return self.amount or 0
