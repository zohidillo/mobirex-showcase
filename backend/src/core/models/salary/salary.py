from django.utils.translation import gettext_lazy as _

from src.bases.models import *


class Salary(BaseModel):
    branch = models.ForeignKey(
        "core.Branch",
        on_delete=models.PROTECT,
        related_name="salaries",
        verbose_name=_("Filial"),
        help_text=_("Filial."),
    )
    employee = models.ForeignKey(
        "CustomUser",
        on_delete=models.PROTECT,
        related_name="received_salaries",
        verbose_name=_("Xodim"),
        help_text=_("Oylik oluvchi xodim."),
    )
    amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        verbose_name=_("Oylik summasi"),
        help_text=_("Oylik summasi."),
    )
    created_by = models.ForeignKey(
        "CustomUser",
        on_delete=models.PROTECT,
        related_name="created_salaries",
        verbose_name=_("Yaratuvchi"),
        help_text=_("Oylikni yaratgan egasi."),
    )
    note = models.TextField(
        null=True,
        blank=True,
        verbose_name=_("Izoh"),
        help_text=_("Ixtiyoriy izoh."),
    )

    class Meta:
        db_table = "salaries"
        verbose_name = _("Oylik")
        verbose_name_plural = _("Oyliklar")
        ordering = ["-added_at"]
        indexes = [
            models.Index(fields=["branch"], name="salary_branch_idx"),
            models.Index(fields=["employee"], name="salary_employee_idx"),
            models.Index(fields=["created_by"], name="salary_created_by_idx"),
            models.Index(fields=["added_at"], name="salary_added_at_idx"),
            models.Index(fields=["is_deleted"], name="salary_is_deleted_idx"),
        ]

    def __str__(self):
        return f"{self.employee} - {self.amount}"
