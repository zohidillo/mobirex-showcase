"""Ro‘yxatdan o‘tmagan foydalanuvchidan kelgan bog‘lanish so‘rovi.

Mavjud ``create_support_request`` oqimiga tegilmaydi — landing sayti, mobil
ilova va Telegram bot o‘sha yo‘ldan yuradi. Bu yerda faqat yangi public
endpoint uchun kerak bo‘lgan qism: anonim ``SupportRequest`` + guruhga xabar.
"""

import logging

from django.db import transaction
from django.utils import timezone

import src.core.models as models
from src.core.constants import get_region_label

from .requests import create_initial_message
from .telegram import notify_contact_request

logger = logging.getLogger(__name__)


def build_contact_message(*, phone, region):
    """CRM ro‘yxatida va Telegramda o‘qishga qulay matn.

    Viloyat alohida ustunda ham saqlanadi, lekin mavjud CRM shablonlari
    faqat ``message`` va ``phone``ni ko‘rsatadi — shuning uchun viloyat shu
    matnga ham yoziladi (shablonlar o‘zgarmaydi).
    """
    region_label = get_region_label(region)
    return f"Yangi so‘rov — {region_label}\nTelefon: {phone}"


def create_public_contact_request(*, phone, region, request=None):
    """Anonim CONTACT murojaatini yaratadi va guruhga xabar beradi."""
    at = timezone.now()
    metadata = {"public_contact": True}
    if request is not None:
        meta = getattr(request, "META", {})
        ip = meta.get("HTTP_X_FORWARDED_FOR") or meta.get("REMOTE_ADDR")
        if ip:
            metadata["request_ip"] = ip.split(",")[0].strip()
        user_agent = meta.get("HTTP_USER_AGENT")
        if user_agent:
            metadata["user_agent"] = user_agent[:255]

    with transaction.atomic():
        support_request = models.SupportRequest.objects.create(
            user=None,
            request_type=models.SupportRequest.RequestType.CONTACT,
            source=models.SupportRequest.Source.PUBLIC_APP,
            phone=phone,
            contact_region=region,
            message=build_contact_message(phone=phone, region=region),
            metadata=metadata,
            status=models.SupportRequest.Status.NEW,
            last_message_at=at,
            last_user_message_at=at,
            user_read_at=None,
            admin_read_at=None,
        )
        create_initial_message(support_request, at=at)

    # Xabar tranzaksiyadan keyin — tarmoq xatosi yozuvni qaytarib olmasin.
    notify_contact_request(support_request)
    return support_request
