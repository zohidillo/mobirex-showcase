from django.conf import settings
from django.db import models
from django.db.models import Q
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from src.bases.models import BaseModel


class ErrorReport(BaseModel):
    class Source(models.TextChoices):
        BACKEND = "BACKEND", _("Backend")
        BACKEND_CELERY = "BACKEND_CELERY", _("Backend Celery")
        MOBILE_ANDROID = "MOBILE_ANDROID", _("Mobile Android")
        MOBILE_IOS = "MOBILE_IOS", _("Mobile iOS")

    class Severity(models.TextChoices):
        INFO = "INFO", _("Info")
        WARNING = "WARNING", _("Warning")
        ERROR = "ERROR", _("Error")
        CRITICAL = "CRITICAL", _("Critical")

    class Kind(models.TextChoices):
        EXCEPTION = "EXCEPTION", _("Exception")
        VALIDATION = "VALIDATION", _("Validation")
        NETWORK = "NETWORK", _("Network")
        OTHER = "OTHER", _("Other")

    source = models.CharField(
        max_length=32,
        choices=Source.choices,
        verbose_name=_("Manba"),
    )
    severity = models.CharField(
        max_length=16,
        choices=Severity.choices,
        default=Severity.ERROR,
        verbose_name=_("Jiddiylik"),
    )
    kind = models.CharField(
        max_length=16,
        choices=Kind.choices,
        default=Kind.EXCEPTION,
        verbose_name=_("Tur"),
    )
    error_type = models.CharField(
        max_length=255,
        verbose_name=_("Xato turi"),
    )
    error_message = models.TextField(
        verbose_name=_("Xato xabari"),
    )
    stack_trace = models.TextField(
        null=True,
        blank=True,
        verbose_name=_("Stack trace"),
    )
    request_path = models.CharField(
        max_length=500,
        null=True,
        blank=True,
        verbose_name=_("So'rov yo'li"),
    )
    request_method = models.CharField(
        max_length=10,
        null=True,
        blank=True,
        verbose_name=_("So'rov metodi"),
    )
    status_code = models.IntegerField(
        null=True,
        blank=True,
        verbose_name=_("Status kodi"),
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="error_reports",
        verbose_name=_("Foydalanuvchi"),
    )
    app_version = models.CharField(
        max_length=32,
        null=True,
        blank=True,
        verbose_name=_("Ilova versiyasi"),
    )
    platform = models.CharField(
        max_length=64,
        null=True,
        blank=True,
        verbose_name=_("Platforma"),
    )
    context = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_("Kontekst"),
    )
    fingerprint = models.CharField(
        max_length=64,
        db_index=True,
        verbose_name=_("Barmoq izi"),
    )
    occurrence_count = models.PositiveIntegerField(
        default=1,
        verbose_name=_("Takrorlanish soni"),
    )
    first_seen_at = models.DateTimeField(
        default=timezone.now,
        verbose_name=_("Birinchi ko'rilgan vaqt"),
    )
    last_seen_at = models.DateTimeField(
        default=timezone.now,
        verbose_name=_("Oxirgi ko'rilgan vaqt"),
    )
    notified_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Xabar yuborilgan vaqt"),
    )

    class Meta:
        db_table = "error_reports"
        verbose_name = _("Xato hisoboti")
        verbose_name_plural = _("Xato hisobotlari")
        ordering = ["-last_seen_at"]
        indexes = [
            models.Index(fields=["source"], name="error_report_source_idx"),
            models.Index(fields=["severity"], name="error_report_severity_idx"),
            models.Index(fields=["kind"], name="error_report_kind_idx"),
            models.Index(fields=["fingerprint"], name="error_report_fp_idx"),
            models.Index(fields=["last_seen_at"], name="error_report_last_seen_idx"),
            models.Index(fields=["user"], name="error_report_user_idx"),
            models.Index(fields=["is_deleted"], name="error_report_is_del_idx"),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["fingerprint"],
                condition=Q(is_deleted=False),
                name="unique_active_error_fingerprint",
            )
        ]

    def __str__(self):
        return f"{self.severity} {self.error_type} ({self.occurrence_count}x)"


class ValidationErrorCounter(BaseModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="validation_error_counters",
        verbose_name=_("Foydalanuvchi"),
    )
    error_type = models.CharField(
        max_length=255,
        verbose_name=_("Xato turi"),
    )
    request_path = models.CharField(
        max_length=500,
        verbose_name=_("So'rov yo'li"),
    )
    count = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Son"),
    )
    window_start = models.DateTimeField(
        default=timezone.now,
        verbose_name=_("Oyna boshlanishi"),
    )
    last_notified_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Oxirgi xabar vaqti"),
    )

    class Meta:
        db_table = "validation_error_counters"
        verbose_name = _("Validatsiya xato hisoblagichi")
        verbose_name_plural = _("Validatsiya xato hisoblagichlari")
        unique_together = [("user", "error_type", "request_path")]
        indexes = [
            models.Index(fields=["user"], name="val_err_counter_user_idx"),
            models.Index(fields=["window_start"], name="val_err_counter_window_idx"),
        ]

    def __str__(self):
        return f"{self.user} — {self.error_type} ({self.count}x)"
