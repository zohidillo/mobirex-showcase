from django.conf import settings
from django.utils.translation import gettext_lazy as _

from src.bases.models import *


class BranchUser(BaseModel):
    ROLE_OWNER = "OWNER"
    ROLE_PHONE_SELLER = "PHONE_SELLER"
    ROLE_ACCESSORY_SELLER = "ACCESSORY_SELLER"
    # ROLE_CASHIER = "CASHIER"

    ROLE_CHOICES = (
        (ROLE_OWNER, _("Egasi")),
        (ROLE_PHONE_SELLER, _("Telefon sotuvchisi")),
        (ROLE_ACCESSORY_SELLER, _("Aksessuar sotuvchisi")),
        # (ROLE_CASHIER, _("Kassir")),
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="branch_roles",
        verbose_name=_("Foydalanuvchi"),
    )
    branch = models.ForeignKey(
        "core.Branch",
        on_delete=models.CASCADE,
        related_name="user_roles",
        verbose_name=_("Filial"),
    )
    role = models.CharField(
        max_length=50,
        choices=ROLE_CHOICES,
        verbose_name=_("Rol"),
    )

    class Meta:
        db_table = "branch_user"
        verbose_name = _("Filial roli")
        verbose_name_plural = _("Filial rollari")
        unique_together = ("user", "branch", "role")
        indexes = [
            models.Index(fields=["branch"], name="branch_user_branch_idx"),
            models.Index(fields=["user"], name="branch_user_user_idx"),
            models.Index(fields=["role"], name="branch_user_role_idx"),
            models.Index(fields=["is_deleted"], name="branch_user_is_deleted_idx"),
            models.Index(fields=["added_at"], name="branch_user_added_at_idx"),
        ]

    def __str__(self):
        return f"{self.user} - {self.branch} - {self.role}"
