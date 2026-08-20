"""Support guruhiga Telegram xabari.

``error_reporting/telegram.py`` bilan bir xil mexanika (requests, timeout=5,
HTML parse_mode, xato → ``logger.warning``), lekin boshqa chat va ixtiyoriy
alohida bot tokeni. Sozlanmagan bo‘lsa — jimgina o‘tkazib yuboradi.

Bu notifier faqat yangi public contact endpointidan chaqiriladi; mavjud
``create_support_request`` oqimi o‘zgarmaydi.
"""

import logging

from django.conf import settings
from django.utils import timezone

from src.core.constants import get_region_label

logger = logging.getLogger(__name__)


class SupportTelegramNotifier:
    def __init__(self):
        # Support guruhiga yozadigan bot xato-kanali botidan boshqa bo‘lishi
        # mumkin. Alohida token berilmasa, umumiy tokenga qaytamiz.
        self.token = getattr(settings, "TELEGRAM_SUPPORT_BOT_TOKEN", "") or getattr(
            settings, "TELEGRAM_BOT_TOKEN", ""
        )
        self.chat_id = getattr(settings, "TELEGRAM_SUPPORT_CHAT_ID", "")
        self.enabled = getattr(settings, "TELEGRAM_NOTIFICATIONS_ENABLED", False)

    def _is_active(self):
        return bool(self.enabled) and bool(self.token) and bool(self.chat_id)

    def send_contact_request(self, support_request):
        """Yangi murojaat haqida guruhga xabar beradi. Hech qachon raise qilmaydi."""
        if not self._is_active():
            return False
        return self._post(self._build_html(support_request))

    def _build_html(self, support_request):
        region = get_region_label(support_request.contact_region) or "—"
        phone = support_request.phone or "—"
        created = (
            timezone.localtime(support_request.added_at).strftime("%Y-%m-%d %H:%M")
            if support_request.added_at
            else "—"
        )
        crm_url = self._crm_url(support_request)

        lines = [
            "📞 <b>Yangi bog‘lanish so‘rovi</b> — ilova (ro‘yxatdan o‘tmagan)",
            f"<b>Telefon:</b> <code>{self._esc(phone)}</code>",
            f"<b>Viloyat:</b> {self._esc(region)}",
            f"<b>Vaqt:</b> {created}",
            f"<b>CRM:</b> #{support_request.id}",
        ]
        if crm_url:
            lines.append(f'<a href="{self._esc(crm_url)}">CRM’da ochish</a>')
        return "\n".join(lines)

    @staticmethod
    def _crm_url(support_request):
        base = (getattr(settings, "CRM_BASE_URL", "") or "").rstrip("/")
        if not base:
            return ""
        try:
            from django.urls import reverse

            return f"{base}{reverse('admin_support_detail', args=[support_request.id])}"
        except Exception:
            return ""

    @staticmethod
    def _esc(text):
        return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    def _post(self, html):
        try:
            import requests as http_requests

            url = f"https://api.telegram.org/bot{self.token}/sendMessage"
            payload = {
                "chat_id": self.chat_id,
                "text": html,
                "parse_mode": "HTML",
                "disable_web_page_preview": True,
            }
            response = http_requests.post(url, json=payload, timeout=5)
            if not response.ok:
                logger.warning(
                    "Support Telegram API xatosi: status=%s body=%.200s",
                    response.status_code,
                    response.text,
                )
                return False
            return True
        except Exception as exc:
            logger.warning("Support Telegram xabar yuborishda xato: %s", exc)
            return False


def notify_contact_request(support_request):
    """Guruhga xabar yuboradi; xatolar chaqiruvchiga chiqmaydi."""
    try:
        return SupportTelegramNotifier().send_contact_request(support_request)
    except Exception as exc:
        logger.warning("Support Telegram notifier ishga tushmadi: %s", exc)
        return False
