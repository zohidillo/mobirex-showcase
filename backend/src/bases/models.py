from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.base_user import BaseUserManager

ROLE_CHOICES = (
    ("OWNER", _("Egasi")),
    ("PHONE_SELLER", _("Telefon sotuvchisi")),
    ("ACCESSORY_SELLER", _("Aksessuar sotuvchisi")),
    ("CASHIER", _("Kassir")),
)

SUB_PLAN_CHOICES = (
    ("MONTHLY", _("Oylik")),
    ("YEARLY", _("Yillik")),
    ("VIP", _("VIP")),
)

SUB_STATUS_CHOICES = (
    ("ACTIVE", _("Faol")),
    ("GRACE", _("Imtiyoz muddati")),
    ("BLOCKED", _("Bloklangan")),
)

SUB_PERIOD_CHOICES = (
    ("MONTHLY", _("Oylik")),
    ("YEARLY", _("Yillik")),
)

ACCOUNT_STATUS_CHOICES = (
    ("active", _("Faol")),
    ("grace", _("Imtiyoz muddati")),
    ("blocked", _("Bloklangan")),
    ("vip", _("Imtiyozli")),
)

TRANSACTION_TYPE_CHOICES = (
    ("daily_charge", _("Kunlik yechim")),
    ("payment", _("To‘lov")),
    ("manual_adjustment", _("Qo‘lda o‘zgartirish")),
)

PAYMENT_TYPE_CHOICES = (
    ("click", _("Click")),
    ("payme", _("Payme")),
    ("paynet", _("Paynet")),
    ("cash", _("Naqd")),
)

PHONE_STORAGE_CHOICES = (
    ("16", _("16 GB")),
    ("32", _("32 GB")),
    ("64", _("64 GB")),
    ("128", _("128 GB")),
    ("256", _("256 GB")),
    ("512", _("512 GB")),
    ("1024", _("1 TB")),
    ("2048", _("2 TB")),
)


class CustomManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False)


class AllObjectsManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset()


class BaseModel(models.Model):
    added_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Yaratilgan vaqt"),
        help_text=_("Yaratilgan sana/vaqt."),
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Yangilangan vaqt"),
        help_text=_("Yangilangan sana/vaqt."),
    )
    is_deleted = models.BooleanField(
        default=False,
        verbose_name=_("O‘chirilgan"),
        help_text=_("Yumshoq o‘chirish holati."),
    )

    objects = CustomManager()
    all_objects = AllObjectsManager()

    def delete(self, using=None, keep_parents=False):
        self.is_deleted = True
        self.save()

    class Meta:
        abstract = True
