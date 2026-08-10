from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from src.bases.models import BaseModel


class SupportRequest(BaseModel):
    class RequestType(models.TextChoices):
        CONTACT = "CONTACT", _("Murojaat")
        ACCOUNT_DELETE = "ACCOUNT_DELETE", _("Account o‘chirish")
        TECHNICAL = "TECHNICAL", _("Texnik masala")

    class Source(models.TextChoices):
        MOBILE_APP = "MOBILE_APP", _("Mobile app")
        LANDING_SITE = "LANDING_SITE", _("Landing site")
        TELEGRAM_BOT = "TELEGRAM_BOT", _("Telegram bot")
        ADMIN = "ADMIN", _("Admin")
        PUBLIC_APP = "PUBLIC_APP", _("Ilova — ro‘yxatdan o‘tmagan")

    class Status(models.TextChoices):
        NEW = "NEW", _("Yangi")
        IN_PROGRESS = "IN_PROGRESS", _("Jarayonda")
        RESOLVED = "RESOLVED", _("Hal qilindi")
        REJECTED = "REJECTED", _("Rad etildi")

    class CloseReason(models.TextChoices):
        SOLVED = "SOLVED", _("Hal qilindi")
        USER_UNREACHABLE = "USER_UNREACHABLE", _("Foydalanuvchi bilan bog‘lanib bo‘lmadi")
        DUPLICATE = "DUPLICATE", _("Takroriy murojaat")
        NOT_RELEVANT = "NOT_RELEVANT", _("Mavzuga aloqasi yo‘q")
        OTHER = "OTHER", _("Boshqa")

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="support_requests",
        verbose_name=_("Foydalanuvchi"),
    )
    request_type = models.CharField(
        max_length=32,
        choices=RequestType.choices,
        verbose_name=_("Murojaat turi"),
    )
    source = models.CharField(
        max_length=32,
        choices=Source.choices,
        default=Source.MOBILE_APP,
        verbose_name=_("Manba"),
    )
    full_name = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name=_("To‘liq ism"),
    )
    phone = models.CharField(
        max_length=32,
        null=True,
        blank=True,
        verbose_name=_("Telefon raqami"),
    )
    contact_region = models.CharField(
        max_length=64,
        null=True,
        blank=True,
        verbose_name=_("Viloyat"),
    )
    message = models.TextField(verbose_name=_("Xabar"))
    status = models.CharField(
        max_length=32,
        choices=Status.choices,
        default=Status.NEW,
        verbose_name=_("Holat"),
    )
    admin_note = models.TextField(
        null=True,
        blank=True,
        verbose_name=_("Admin izohi"),
    )
    metadata = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_("Qo‘shimcha ma'lumot"),
    )
    user_read_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Foydalanuvchi o‘qigan vaqt"),
    )
    admin_read_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Admin o‘qigan vaqt"),
    )
    last_message_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Oxirgi xabar vaqti"),
    )
    last_admin_reply_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Oxirgi admin javobi vaqti"),
    )
    last_user_message_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Oxirgi foydalanuvchi xabari vaqti"),
    )
    closed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Yopilgan vaqt"),
    )
    closed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="closed_support_requests",
        verbose_name=_("Yopgan admin"),
    )
    close_reason = models.CharField(
        max_length=32,
        choices=CloseReason.choices,
        null=True,
        blank=True,
        verbose_name=_("Yopilish sababi"),
    )
    close_reason_note = models.TextField(
        null=True,
        blank=True,
        verbose_name=_("Yopilish izohi"),
    )

    class Meta:
        db_table = "support_requests"
        verbose_name = _("Murojaat")
        verbose_name_plural = _("Murojaatlar")
        ordering = ["-added_at"]
        indexes = [
            models.Index(fields=["request_type"], name="support_req_type_idx"),
            models.Index(fields=["source"], name="support_req_source_idx"),
            models.Index(fields=["status"], name="support_req_status_idx"),
            models.Index(fields=["user"], name="support_req_user_idx"),
            models.Index(fields=["phone"], name="support_req_phone_idx"),
            models.Index(fields=["added_at"], name="support_req_added_at_idx"),
            models.Index(fields=["last_message_at"], name="support_req_last_msg_idx"),
            models.Index(fields=["user_read_at"], name="support_req_user_read_idx"),
            models.Index(fields=["admin_read_at"], name="support_req_admin_read_idx"),
        ]

    def __str__(self):
        sender = self.phone or self.full_name or _("Noma'lum")
        created = timezone.localtime(self.added_at).strftime("%Y-%m-%d") if self.added_at else ""
        return f"{self.get_request_type_display()} - {sender} - {created}"

    @property
    def unread_for_user(self):
        if not self.last_admin_reply_at:
            return False
        return self.user_read_at is None or self.user_read_at < self.last_admin_reply_at

    @property
    def unread_for_admin(self):
        if not self.last_user_message_at:
            return False
        return self.admin_read_at is None or self.admin_read_at < self.last_user_message_at


class SupportRequestMessage(BaseModel):
    class SenderType(models.TextChoices):
        USER = "USER", _("Foydalanuvchi")
        ADMIN = "ADMIN", _("Admin")
        SYSTEM = "SYSTEM", _("System")
        EXTERNAL = "EXTERNAL", _("Tashqi manba")

    request = models.ForeignKey(
        SupportRequest,
        on_delete=models.CASCADE,
        related_name="messages",
        verbose_name=_("Murojaat"),
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="support_request_messages",
        verbose_name=_("Yuboruvchi"),
    )
    sender_type = models.CharField(
        max_length=16,
        choices=SenderType.choices,
        verbose_name=_("Yuboruvchi turi"),
    )
    message = models.TextField(verbose_name=_("Xabar"))
    metadata = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_("Qo‘shimcha ma'lumot"),
    )

    class Meta:
        db_table = "support_request_messages"
        verbose_name = _("Murojaat xabari")
        verbose_name_plural = _("Murojaat xabarlari")
        ordering = ["added_at", "id"]
        indexes = [
            models.Index(fields=["request"], name="support_msg_request_idx"),
            models.Index(fields=["sender_type"], name="support_msg_sender_type_idx"),
            models.Index(fields=["added_at"], name="support_msg_added_at_idx"),
        ]

    def __str__(self):
        created = timezone.localtime(self.added_at).strftime("%Y-%m-%d %H:%M") if self.added_at else ""
        return f"{self.get_sender_type_display()} - {created}"
