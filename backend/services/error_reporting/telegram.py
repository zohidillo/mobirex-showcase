import json
import logging

from django.conf import settings

logger = logging.getLogger(__name__)

_SEVERITY_EMOJI = {
    "INFO": "🔵",
    "WARNING": "🟡",
    "ERROR": "🔴",
    "CRITICAL": "🆘",
}

_SOURCE_EMOJI = {
    "BACKEND": "🖥",
    "BACKEND_CELERY": "⏰",
    "MOBILE_ANDROID": "📱",
    "MOBILE_IOS": "📱",
}


class TelegramNotifier:
    def __init__(self):
        self.token = getattr(settings, "TELEGRAM_BOT_TOKEN", "")
        self.chat_id = getattr(settings, "TELEGRAM_LOG_CHAT_ID", "")
        self.enabled = getattr(settings, "TELEGRAM_NOTIFICATIONS_ENABLED", False)

    def _is_active(self):
        return bool(self.enabled) and bool(self.token) and bool(self.chat_id)

    def send_error_report(self, report):
        if not self._is_active():
            return
        self._post(self._build_html(report))

    def _build_html(self, report):
        severity_emoji = _SEVERITY_EMOJI.get(report.severity, "🔴")
        source_emoji = _SOURCE_EMOJI.get(report.source, "🖥")

        username, user_id, roles_csv, branches_csv = "—", "—", "—", "—"
        if report.user:
            username = getattr(report.user, "username", None) or "—"
            user_id = str(report.user.pk)
            try:
                branch_roles = (
                    report.user.branch_roles.filter(is_deleted=False)
                    .select_related("branch")
                )
                roles_csv = ", ".join(sorted({bu.role for bu in branch_roles})) or "—"
                branches_csv = ", ".join(bu.branch.name for bu in branch_roles) or "—"
            except Exception:
                pass

        method = report.request_method or ""
        path = report.request_path or "—"
        status = str(report.status_code) if report.status_code else "—"
        app_ver = report.app_version or "—"
        platform = report.platform or "—"
        first_seen = (
            report.first_seen_at.strftime("%Y-%m-%d %H:%M:%S")
            if report.first_seen_at
            else "—"
        )
        ctx_json = json.dumps(report.context, ensure_ascii=False, indent=2) if report.context else "{}"
        msg_truncated = (report.error_message or "")[:500]

        return (
            f"{source_emoji} {severity_emoji} <b>{report.severity}</b> — {report.source} — {report.kind}\n"
            f"<b>Type:</b> <code>{self._esc(report.error_type)}</code>\n"
            f"<b>Path:</b> <code>{self._esc(method)} {self._esc(path)}</code>\n"
            f"<b>Status:</b> {status}\n"
            f"<b>User:</b> {self._esc(username)} (id={user_id})\n"
            f"<b>Roles:</b> {self._esc(roles_csv)}\n"
            f"<b>Branches:</b> {self._esc(branches_csv)}\n"
            f"<b>App:</b> {self._esc(app_ver)} {self._esc(platform)}\n"
            f"<b>Count:</b> {report.occurrence_count}x\n"
            f"<b>First seen:</b> {first_seen}\n"
            f"<b>Context:</b>\n<pre>{self._esc(ctx_json)}</pre>\n"
            f"<b>Message:</b>\n<pre>{self._esc(msg_truncated)}</pre>"
        )

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
                    "Telegram API xatosi: status=%s body=%.200s",
                    response.status_code,
                    response.text,
                )
        except Exception as exc:
            logger.warning("Telegram xabar yuborishda xato: %s", exc)
