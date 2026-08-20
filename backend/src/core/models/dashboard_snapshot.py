from django.utils.translation import gettext_lazy as _

from src.bases.models import *


class DashboardSnapshot(models.Model):
    branch = models.ForeignKey(
        "core.Branch",
        on_delete=models.CASCADE,
        related_name="dashboard_snapshots",
        verbose_name=_("Filial"),
        help_text=_("Snapshot tegishli filial."),
    )
    month = models.DateField(
        verbose_name=_("Oy"),
        help_text=_("Dashboard snapshot oyi (oyning birinchi kuni)."),
    )
    dashboard_data = models.JSONField(
        default=dict,
        verbose_name=_("Dashboard ma’lumotlari"),
        help_text=_("Filial dashboardining saqlangan holati."),
    )
    phone_data = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_("Telefon dashboard ma’lumotlari"),
        help_text=_("Telefon dashboardining saqlangan holati."),
    )
    accessory_data = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_("Aksessuar dashboard ma’lumotlari"),
        help_text=_("Aksessuar dashboardining saqlangan holati."),
    )
    debt_data = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_("Qarz ma’lumotlari"),
        help_text=_("Qarz bo‘limining saqlangan holati."),
    )
    expense_data = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_("Xarajat ma’lumotlari"),
        help_text=_("Xarajat bo‘limining saqlangan holati."),
    )
    salary_data = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_("Maosh ma’lumotlari"),
        help_text=_("Maosh bo‘limining saqlangan holati."),
    )
    capital_data = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_("Kapital ma’lumotlari"),
        help_text=_("Kapital bo‘limining saqlangan holati."),
    )
    is_locked = models.BooleanField(
        default=True,
        verbose_name=_("Qulflangan"),
        help_text=_("Snapshot oyi muzlatilganligini bildiradi."),
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Yaratilgan vaqt"),
        help_text=_("Snapshot yaratilgan vaqt."),
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Yangilangan vaqt"),
        help_text=_("Snapshot yangilangan vaqt."),
    )

    class Meta:
        db_table = "dashboard_snapshots"
        verbose_name = _("Dashboard snapshot")
        verbose_name_plural = _("Dashboard snapshotlar")
        ordering = ["-month", "-created_at", "-id"]
        constraints = [
            models.UniqueConstraint(
                fields=["branch", "month"],
                name="unique_branch_month_dashboard_snapshot",
            ),
        ]
        indexes = [
            models.Index(fields=["branch", "month"], name="dash_snap_branch_month_idx"),
        ]

    def save(self, *args, **kwargs):
        if self.month:
            self.month = self.month.replace(day=1)
        return super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.branch} - {self.month}"
