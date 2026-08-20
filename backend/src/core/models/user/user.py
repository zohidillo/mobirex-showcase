from functools import cached_property
from decimal import Decimal

from django.contrib.auth.hashers import check_password, make_password
from django.utils.translation import gettext_lazy as _

from src.bases.models import *


# Shared review logins seeded by `generate_demo`. Identified by username because
# there is no dedicated column; kept here as the single source of truth.
DEMO_USERNAMES = frozenset({"demo_owner", "demo_phone", "demo_accessory"})


class CustomUserManager(BaseUserManager):
    use_in_migrations = True

    def create_user(self, username, password=None, **extra_fields):
        if not username:
            raise ValueError(_("Foydalanuvchi nomi kiritilishi shart."))
        extra_fields.setdefault("is_active", True)
        user = self.model(username=username, **extra_fields)

        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError(_("Superuser uchun is_staff=True bo‘lishi shart."))
        if extra_fields.get("is_superuser") is not True:
            raise ValueError(_("Superuser uchun is_superuser=True bo‘lishi shart."))

        return self.create_user(username, password, **extra_fields)


class CustomUser(AbstractUser, BaseModel):
    THEME_SYSTEM = "system"
    THEME_LIGHT = "light"
    THEME_DARK = "dark"

    THEME_CHOICES = (
        (THEME_SYSTEM, _("System")),
        (THEME_LIGHT, _("Light")),
        (THEME_DARK, _("Dark")),
    )

    balance = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=Decimal("0.00"),
        verbose_name=_("Balans"),
        help_text=_("Foydalanuvchining joriy balansi."),
    )
    grace_start_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_("Imtiyoz boshlanish sanasi"),
        help_text=_("Balans manfiy bo‘lganda boshlangan sana."),
    )
    account_status = models.CharField(
        max_length=16,
        choices=ACCOUNT_STATUS_CHOICES,
        default="active",
        verbose_name=_("Hisob holati"),
        help_text=_("Billing bo‘yicha joriy hisob holati."),
    )
    daily_fee = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=Decimal("3300.00"),
        verbose_name=_("Kunlik to‘lov"),
        help_text=_("Har kuni yechiladigan summa."),
    )
    is_vip = models.BooleanField(
        default=False,
        verbose_name=_("VIP"),
        help_text=_("VIP foydalanuvchilar bepul va bloklanmaydi."),
    )
    phone = models.CharField(
        max_length=32,
        null=True,
        blank=True,
        verbose_name=_("Telefon raqami"),
        help_text=_("Ixtiyoriy telefon raqami."),
    )
    is_cashier = models.BooleanField(
        default=False,
        verbose_name=_("Kassir"),
        help_text=_("Ushbu foydalanuvchi tizim kassiri."),
    )
    theme = models.CharField(
        max_length=16,
        choices=THEME_CHOICES,
        default=THEME_SYSTEM,
        verbose_name=_("Tema"),
        help_text=_("Mobil ilova uchun tanlangan tema."),
    )
    mobile_pin_hash = models.CharField(
        max_length=128,
        null=True,
        blank=True,
        verbose_name=_("Mobil PIN xeshi"),
        help_text=_("Mobil ilova uchun 4 xonali PIN xeshi."),
    )
    deleted_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("O‘chirilgan vaqt"),
        help_text=_("Foydalanuvchi hisobi o‘chirilgan sana/vaqt."),
    )

    objects = CustomUserManager()

    class Meta:
        db_table = "custom_users"
        verbose_name = _("Foydalanuvchi")
        verbose_name_plural = _("Foydalanuvchilar")
        ordering = ["-added_at"]

    def __str__(self):
        return self.get_username()

    @property
    def has_pin(self):
        return bool(self.mobile_pin_hash)

    @property
    def is_demo(self):
        """Whether this is a shared demo/review account with restricted actions."""
        return self.username in DEMO_USERNAMES

    def has_role(self, role, branch=None):
        if branch is not None:
            branch_id = getattr(branch, "id", branch)
            return branch_id in self._role_branch_map.get(role, set())
        return role in self.roles

    @cached_property
    def roles(self):
        return set(self._role_branch_map.keys())

    @cached_property
    def _role_branch_map(self):
        role_map = {}
        for role, branch_id in (
            self.branch_roles.filter(is_deleted=False).values_list("role", "branch_id")
        ):
            role_map.setdefault(role, set()).add(branch_id)
        return role_map

    def get_branch(self, role=None):
        qs = self.branch_roles.filter(is_deleted=False)
        if role:
            qs = qs.filter(role=role)
        obj = qs.first()
        return obj.branch if obj else None

    def get_primary_branch(self, role=None):
        return self.get_branch(role)

    def get_all_branches(self, role=None):
        qs = self.branch_roles.filter(is_deleted=False)
        if role:
            qs = qs.filter(role=role)
        return [x.branch for x in qs.select_related("branch")]

    @property
    def subscription_status(self):
        if self.is_billing_vip:
            return "VIP"
        return (self.account_status or "active").upper()

    def get_subscription_status_display(self):
        return self.get_account_status_display()

    @property
    def is_billing_vip(self):
        return self.is_vip or self.account_status == "vip"

    def set_mobile_pin(self, pin):
        self.mobile_pin_hash = make_password(pin)

    def check_mobile_pin(self, pin):
        if not self.mobile_pin_hash:
            return False
        return check_password(pin, self.mobile_pin_hash)
