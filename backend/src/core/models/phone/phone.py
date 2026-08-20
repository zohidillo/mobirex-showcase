from django.utils.translation import gettext_lazy as _

from src.bases.models import *


class Phone(BaseModel):
    name = models.CharField(
        max_length=255,
        verbose_name=_("Model"),
        help_text=_("Telefon modeli nomi."),
    )
    category = models.ForeignKey(
        "core.PhoneCategory",
        on_delete=models.PROTECT,
        related_name="phones",
        verbose_name=_("Kategoriya"),
        help_text=_("Telefon kategoriyasi."),
    )
    branch = models.ForeignKey(
        "core.Branch",
        on_delete=models.PROTECT,
        related_name="phones",
        verbose_name=_("Filial"),
        help_text=_("Telefon tegishli filial."),
    )
    imei = models.CharField(
        max_length=64,
        verbose_name=_("IMEI"),
        help_text=_("Telefon IMEI raqami."),
    )
    storage = models.CharField(
        max_length=64,
        verbose_name=_("Xotira"),
        help_text=_("Telefon xotirasi (masalan: 128GB)."),
        choices=PHONE_STORAGE_CHOICES,
    )
    color = models.CharField(
        max_length=64,
        null=True,
        blank=True,
        verbose_name=_("Rang"),
        help_text=_("Telefon rangi."),
    )
    from_by = models.CharField(
        max_length=255,
        verbose_name=_("Qayerdan olingan"),
        help_text=_("Telefon qayerdan xarid qilingan."),
    )
    cost_price = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        verbose_name=_("Tannarx"),
        help_text=_("Telefon xarid tannarxi."),
    )
    sell_price = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Sotuv narxi"),
        help_text=_("Telefon sotuv narxi."),
    )
    is_sold = models.BooleanField(
        default=False,
        verbose_name=_("Sotilgan"),
        help_text=_("Telefon sotilganligi."),
    )
    for_month_close = models.BooleanField(
        default=False,
        verbose_name=_("Oy yopilishi orqali ko’chirilgan"),
        help_text=_("Telefon oy yopilishida keyingi oyga ko’chirilganligini bildiradi."),
    )
    is_month_closed = models.BooleanField(
        default=False,
        verbose_name=_("Oy yopilgan"),
        help_text=_("Telefon oy yopilishida yopilgan va keyingi oyga ko’chirilgan."),
    )
    month_closed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Oy yopilgan vaqt"),
        help_text=_("Telefon oy yopilishida yopilgan vaqt."),
    )
    rolled_over_from = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="rollovers",
        verbose_name=_("Ko’chirilgan manba"),
        help_text=_("Bu telefon qaysi eski telefondan ko’chirilganligi."),
    )
    added_by = models.ForeignKey(
        "CustomUser",
        on_delete=models.PROTECT,
        related_name="added_phones",
        verbose_name=_("Qo‘shgan foydalanuvchi"),
        help_text=_("Telefonni qo‘shgan foydalanuvchi."),
    )
    sold_by = models.ForeignKey(
        "CustomUser",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="sold_phones",
        verbose_name=_("Sotgan foydalanuvchi"),
        help_text=_("Telefonni sotgan foydalanuvchi."),
    )
    sold_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Sotilgan vaqt"),
        help_text=_("Telefon sotilgan sana/vaqti."),
    )

    class Meta:
        db_table = "phones"
        verbose_name = _("Telefon")
        verbose_name_plural = _("Telefonlar")
        ordering = ["-added_at"]
        indexes = [
            models.Index(fields=["branch", "is_sold"]),
            models.Index(fields=["sold_at"]),
            models.Index(fields=["is_deleted"], name="phone_is_deleted_idx"),
            models.Index(fields=["branch", "added_at"], name="phone_branch_added_at_idx"),
            models.Index(fields=["branch", "is_month_closed"], name="phone_branch_month_closed_idx"),
        ]

    def __str__(self):
        return f"{self.name} - {self.imei}"

    @property
    def created_by(self):
        return self.added_by

    @property
    def profit(self):
        sell = self.sell_price or 0
        cost = self.cost_price or 0
        return sell - cost

    @property
    def is_profitable(self):
        return self.profit > 0
