import re

from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from src.core.constants import REGION_CHOICES, REGION_VALUES


# O‘zbekiston mobil operator kodlari.
UZ_MOBILE_CODES = frozenset(
    {
        "20",  # Humans
        "33",  # Humans / Mobiuz
        "50",  # Uzmobile
        "55",  # Humans / Perfectum
        "77",  # Uzmobile
        "88",  # Mobiuz
        "90",  # Beeline
        "91",  # Beeline
        "93",  # Ucell
        "94",  # Ucell
        "95",  # Uzmobile / Mobiuz
        "97",  # Mobiuz
        "98",  # Uzmobile
        "99",  # Uzmobile
    }
)

# Shahar (statsionar) kodlari. Do‘konlarda ko‘pincha aynan shu raqam
# bo‘ladi — rad etsak, egasi bog‘lanish so‘rovini qoldira olmaydi.
UZ_CITY_CODES = frozenset(
    {
        "71",  # Toshkent shahri
        "78",  # Toshkent shahri
        "61",  # Andijon
        "62",  # Buxoro
        "65",  # Samarqand
        "66",  # Navoiy
        "67",  # Jizzax
        "69",  # Qarshi
        "70",  # Namangan
        "72",  # Farg‘ona
        "73",  # Xorazm
        "74",  # Termiz
        "75",  # Guliston
        "76",  # Nukus
    }
)

# Qabul qilinadigan barcha kodlar. "Har qanday 2 xona" tekshiruvi
# 998012345678 kabi mavjud bo‘lmagan raqamlarni o‘tkazib yuborardi.
UZ_PHONE_CODES = UZ_MOBILE_CODES | UZ_CITY_CODES

_UZ_PHONE_RE = re.compile(r"^998(\d{2})(\d{7})$")
_SEPARATORS_RE = re.compile(r"[\s\-()]+")


def normalize_uz_phone(raw):
    """Turli formatdagi raqamni yagona ``+998XXXXXXXXX`` ko‘rinishiga keltiradi.

    Qabul qilinadi: ``+998901234567``, ``998901234567``, ``901234567``, va
    bo‘shliq/defis/qavs bilan yozilgan variantlar. Mobil ham, shahar
    (statsionar) raqami ham bo‘lishi mumkin. Mos kelmasa ``None``.
    """
    if not raw:
        return None

    digits = _SEPARATORS_RE.sub("", str(raw)).strip()
    if digits.startswith("+"):
        digits = digits[1:]
    if not digits.isdigit():
        return None

    if len(digits) == 9:
        digits = f"998{digits}"
    elif len(digits) == 12 and digits.startswith("998"):
        pass
    else:
        return None

    match = _UZ_PHONE_RE.match(digits)
    if not match or match.group(1) not in UZ_PHONE_CODES:
        return None
    return f"+{digits}"


class PublicContactRequestSerializer(serializers.Serializer):
    """Public bog‘lanish so‘rovi — faqat telefon va viloyat.

    ``Serializer`` (``ModelSerializer`` emas) — bu endpoint ochiq, shuning
    uchun modelning boshqa maydonlariga yo‘l bo‘lmasligi kerak.
    """

    phone = serializers.CharField(max_length=32)
    region = serializers.CharField(max_length=64)

    def validate_phone(self, value):
        normalized = normalize_uz_phone(value)
        if not normalized:
            raise serializers.ValidationError(
                _("Telefon raqami noto‘g‘ri. Namuna: +998901234567")
            )
        return normalized

    def validate_region(self, value):
        value = (value or "").strip()
        if value not in REGION_VALUES:
            raise serializers.ValidationError(_("Viloyat noto‘g‘ri tanlangan."))
        return value

    def validate(self, attrs):
        # Ortiqcha maydonlarni rad etamiz — endpoint ochiq, kutilmagan
        # kalitlar jimgina yutilmasin.
        unknown = set(self.initial_data) - set(self.fields)
        if unknown:
            raise serializers.ValidationError(
                {
                    field: _("Bu maydon qabul qilinmaydi.")
                    for field in sorted(unknown)
                }
            )
        return attrs


class RegionSerializer(serializers.Serializer):
    value = serializers.CharField()
    label = serializers.CharField()


class RegionListSerializer(serializers.Serializer):
    regions = RegionSerializer(many=True)


def get_region_payload():
    """Return the region list in API shape."""
    return [{"value": value, "label": label} for value, label in REGION_CHOICES]
