from django.utils.translation import gettext_lazy as _

from src.bases.models import *


class Subscription(BaseModel):
    user = models.ForeignKey(
        "CustomUser",
        on_delete=models.CASCADE,
        related_name="subscriptions",
        verbose_name=_("Foydalanuvchi"),
        help_text=_("Obuna foydalanuvchisi."),
    )
    plan_type = models.CharField(
        max_length=16,
        choices=SUB_PLAN_CHOICES,
        verbose_name=_("Reja turi"),
        help_text=_("Obuna reja turi."),
    )
    start_date = models.DateTimeField(
        verbose_name=_("Boshlanish vaqti"),
        help_text=_("Obuna boshlanish sanasi/vaqti."),
    )
    end_date = models.DateTimeField(
        verbose_name=_("Tugash vaqti"),
        help_text=_("Obuna tugash sanasi/vaqti."),
    )
    grace_end_date = models.DateTimeField(
        verbose_name=_("Imtiyoz muddati tugashi"),
        help_text=_("Imtiyoz muddati tugash sanasi/vaqti."),
    )
    status = models.CharField(
        max_length=16,
        choices=SUB_STATUS_CHOICES,
        verbose_name=_("Holat"),
        help_text=_("Obuna holati."),
    )

    class Meta:
        db_table = "subscriptions"
        verbose_name = _("Obuna")
        verbose_name_plural = _("Obunalar")
        ordering = ["-added_at"]
        indexes = [
            models.Index(fields=["user"], name="subscription_user_idx"),
            models.Index(fields=["status"], name="subscription_status_idx"),
            models.Index(fields=["end_date"], name="subscription_end_date_idx"),
            models.Index(fields=["added_at"], name="subscription_added_at_idx"),
            models.Index(fields=["is_deleted"], name="subscription_is_deleted_idx"),
        ]

    def __str__(self):
        return f"{self.user.get_username()} - {self.status} - {self.end_date}"

    @property
    def is_active(self):
        return self.status == "ACTIVE"

    @property
    def in_grace(self):
        return self.status == "GRACE"
