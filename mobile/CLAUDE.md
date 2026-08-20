# Mobirex Backend — Telegram Error Reporting (audit-first, zero-surprise)

## Kontekst

Bu ishlab turgan production tizim. Sen CLAUDE.md ichidagi BARCHA qoidalarga
qattiq amal qilasan, ayniqsa:

- Audit first, fix after report
- Hech narsa OCHMA — mavjud endpoint, model, URL, service signaturesini
  o'zgartirma
- Yangi Django app YARATMA — bizda bitta `src/core/` app bor
- Mavjud kod konvensiyasiga o'xshatib yoz
- Test qilishni unutma — `pytest` natijasini ko'rsat
- Audit tugaguncha hech narsa yozma yoki yaratma

Eslatma: Sen `crm/` papkasidasan. `pwd` bilan tekshir. `manage.py`
bo'lishi shart.

## Vazifa qisqacha

Backend'da error reporting tizimi qil. Backend va mobile app'dan kelgan
xatolar bitta Telegram kanaliga yuboriladi.

- Bitta yangi model: `ErrorReport` (src/core/models/ ichida, mavjud
  pattern'da)
- Bitta service: `src/services/error_reporting/` (yangi feature service)
- Bitta API endpoint: `POST /api/error-report/` — mobile'dan qabul qiladi
- Django logging handler — server-side 500 errorlar uchun
- Telegram notifier — env'dan token/chat_id oladi, yo'q bo'lsa silent skip

## 1-bosqich: AUDIT (kod yozma)

Quyidagilarni o'qi va men uchun audit hisobotini yoz:

a) `src/core/models/support_request.py` — bu shunga o'xshash structured
   model, qaysi pattern'da yozilganini ko'r (BaseModel, choices,
   TextChoices, Meta.indexes, __str__, property'lar)

b) `src/core/models/__init__.py` — yangi model bu yerda qanday export
   qilinadi

c) `src/core/models/phone/phone.py` va `src/core/models/accessory/accessory.py`
   — model fayl pattern'i (yagona faylmi yoki sub-papka'mi)

d) `src/services/phone/create.py` va `src/services/debt/create.py` —
   service pattern (transaction.atomic, _snapshot helper,
   JournalService.log_create)

e) `src/services/__init__.py` agar mavjud bo'lsa — yangi service shu
   yerda qanday register qilinadi

f) `src/api/views/support/` papkasi (bo'lishi kerak) — view pattern
   (BaseAPIView, extend_schema, permission_classes, success/error helper)

g) `src/api/urls/support.py` va `src/api/urls/__init__.py` — URL ulash
   pattern

h) `src/api/serializers/support/` papkasi — serializer pattern

i) `src/api/base.py` va `src/api/responses.py` — BaseAPIView va response
   helper'lar nima

j) `src/api/throttles.py` va `config/settings/local.py` ichidagi
   REST_FRAMEWORK DEFAULT_THROTTLE_RATES — throttle qanday qo'shiladi

k) `src/bases/models.py` — BaseModel nima beradi (added_at, updated_at,
   is_deleted bor)

l) `config/settings/local.py` ichida LOGGING konfiguratsiyasi nima — yangi
   handler qaysi pattern'da qo'shiladi

m) `.env.dev` va `.env.example` (agar bor bo'lsa) — env qanday yoziladi

n) `tests/api/support/` va `tests/conftest.py` — test pattern (qaysi
   fixture'lar bor, authenticated_client, mock helper)

Audit oxirida menga shu narsalarni qaytarib bering:

1. Yangi model `ErrorReport`'ni qaysi yo'lga joylashtirasan
   (`src/core/models/error_report.py` yoki sub-papka)
2. Service papkasi nomi va structure
3. View va URL va serializer joylari aniq
4. Settings qaysi joyga TG token/chat_id qo'shiladi
5. Logging handler aynan qaysi konfiguratsiya qatoriga qo'shiladi
6. Test fayl(lari) nomi va joyi
7. Migration komandasi qachon ishlatiladi va qanday tekshiriladi
8. Tahmindagi fayllar ro'yxati (qancha yangi, qancha o'zgargan)

Men `OK, davom et` deyishimni kut. Mendan boshqa hech qanday tasdiq
kelmaguncha kod yozma.

## 2-bosqich: Implementatsiya (faqat tasdiqdan keyin)

### Model: ErrorReport

`src/bases/models.py` ichidagi `BaseModel`'dan meros olsin
(`added_at`, `updated_at`, `is_deleted` keladi).

Fieldlar (TextChoices class ichida, `SupportRequest` pattern'i bo'yicha):

class Source(TextChoices):
    BACKEND = "BACKEND", _("Backend")
    MOBILE_ANDROID = "MOBILE_ANDROID", _("Mobile Android")
    MOBILE_IOS = "MOBILE_IOS", _("Mobile iOS")

class Severity(TextChoices):
    INFO = "INFO", _("Info")
    WARNING = "WARNING", _("Warning")
    ERROR = "ERROR", _("Error")
    CRITICAL = "CRITICAL", _("Critical")

Fieldlar:
- source: CharField(max_length=32, choices=Source.choices)
- severity: CharField(max_length=16, choices=Severity.choices,
  default=Severity.ERROR)
- error_type: CharField(max_length=255) — masalan "DioException",
  "ValidationError", "DatabaseError", "500"
- error_message: TextField — qisqartirilgan xabar
- stack_trace: TextField(null=True, blank=True)
- request_path: CharField(max_length=500, null=True, blank=True)
- request_method: CharField(max_length=10, null=True, blank=True)
- status_code: IntegerField(null=True, blank=True)
- user: FK(settings.AUTH_USER_MODEL, on_delete=SET_NULL, null=True,
  blank=True, related_name="error_reports")
- app_version: CharField(max_length=32, null=True, blank=True)
- platform: CharField(max_length=64, null=True, blank=True)
- context: JSONField(default=dict, blank=True)
- fingerprint: CharField(max_length=64, db_index=True) — hash
- occurrence_count: PositiveIntegerField(default=1)
- first_seen_at: DateTimeField(default=timezone.now)
- last_seen_at: DateTimeField(default=timezone.now)
- notified_at: DateTimeField(null=True, blank=True)

Meta:
- db_table = "error_reports"
- verbose_name, verbose_name_plural (uzbek)
- ordering = ["-last_seen_at"]
- indexes: source, severity, fingerprint, last_seen_at, user, is_deleted
- constraints: UniqueConstraint(fields=["fingerprint"],
  condition=Q(is_deleted=False), name="unique_active_error_fingerprint")

__str__: f"{severity} {error_type} ({occurrence_count}x)"

`src/core/models/__init__.py` ga export qo'sh.

### Service: ErrorReportingService

`src/services/error_reporting/__init__.py` va modullari:

- `service.py` — ErrorReportingService klass
- `telegram.py` — TelegramNotifier klass
- `logging_handler.py` — TelegramLoggingHandler (Python logging.Handler)
- `fingerprint.py` — hash logic

### ErrorReportingService.report_error()

@staticmethod
def report_error(
    *,
    source,
    error_type,
    error_message,
    severity="ERROR",
    stack_trace=None,
    request_path=None,
    request_method=None,
    status_code=None,
    user=None,
    app_version=None,
    platform=None,
    context=None,
):
    # 1. Fingerprint hisobla (fingerprint.py'dagi compute_fingerprint)
    # 2. transaction.atomic + select_for_update
    # 3. Active ErrorReport'ni fingerprint bo'yicha qidir
    # 4. Topilsa: occurrence_count += 1, last_seen_at = now, save
    # 5. Yo'q bo'lsa: yangi yarat
    # 6. should_notify() ni hisobla
    # 7. Notify bo'lsa: TelegramNotifier.send orqali yubor; notified_at
    #    yangilansin. Network error bo'lsa silently caught.
    # 8. ErrorReport ob'ektini qaytar

### should_notify(report)

- report.severity == CRITICAL → True
- report.occurrence_count == 1 → True
- report.occurrence_count in (10, 100, 1000) → True
- report.notified_at va now - notified_at < 5 daqiqa → False (rate limit)
- aks holda False

### TelegramNotifier

- __init__ env'dan TELEGRAM_BOT_TOKEN, TELEGRAM_LOG_CHAT_ID,
  TELEGRAM_NOTIFICATIONS_ENABLED oladi
- enabled=False yoki token yo'q → send() no-op (silent skip)
- send_error_report(report) — HTML xabar yasaydi va Telegram bot API'ga
  POST qiladi:
  https://api.telegram.org/bot{TOKEN}/sendMessage
  payload: {"chat_id": CHAT_ID, "text": html, "parse_mode": "HTML",
            "disable_web_page_preview": True}
- timeout 5 soniya
- HTTP 4xx/5xx, ConnectionError, Timeout — silently caught va log
  (faqat logger.warning, error reporting cycle YO'Q)

HTML shabloni:

🔴 {severity_emoji} <b>{severity}</b> — {source}
<b>Type:</b> <code>{error_type}</code>
<b>Path:</b> <code>{method} {path}</code>
<b>Status:</b> {status_code}
<b>User:</b> {username} (id={user_id})
<b>Roles:</b> {roles_csv}
<b>Branches:</b> {branches_csv}
<b>App:</b> {app_version} {platform}
<b>Count:</b> {count}x
<b>First seen:</b> {first_seen}
<b>Context:</b>
<pre>{context_json}</pre>
<b>Message:</b>
<pre>{error_message_truncated_500}</pre>

Severity emoji: INFO=🔵, WARNING=🟡, ERROR=🔴, CRITICAL=🆘

### TelegramLoggingHandler (Python logging.Handler)

class TelegramLoggingHandler(logging.Handler):
    def emit(self, record):
        try:
            # Recursion'dan saqlash uchun shu klassdan kelgan logni
            # qabul qilma (record.name shu modulning logger'i bo'lsa skip)
            if record.name.startswith("src.services.error_reporting"):
                return
            ErrorReportingService.report_error(
                source="BACKEND",
                severity=self._map_level(record.levelno),
                error_type=record.levelname,
                error_message=self.format(record),
                stack_trace=self._extract_stack(record),
                context={"logger": record.name, "module": record.module},
            )
        except Exception:
            # Logging handler hech qachon raise qilmaydi
            pass

`config/settings/local.py` LOGGING blockida:
- formatters'ga oddiy "verbose" formatter qo'sh
- handlers'ga "telegram" handler qo'sh:
  - class: "src.services.error_reporting.logging_handler.TelegramLoggingHandler"
  - level: "ERROR"
- loggers["django.request"] ga ["telegram"] qo'sh (eski handler'larni
  saqlab qoldir — propagate False bo'lmasin)

### API endpoint: POST /api/error-report/

`src/api/views/error_reporting/views.py`:

ErrorReportSerializer:
- severity (default ERROR)
- error_type (required)
- error_message (required)
- stack_trace (optional)
- request_path (optional)
- request_method (optional)
- status_code (optional)
- app_version (optional)
- platform (optional) — "android" yoki "ios"
- context (optional, dict)

ErrorReportCreateAPIView(BaseAPIView):
- permission_classes = [IsAuthenticated]
- throttle_classes = [ScopedRateThrottle]
- throttle_scope = "error_report"
- @extend_schema with tags=["Error Reporting"], request, responses
- def post(self, request):
    serializer.is_valid()
    source = "MOBILE_ANDROID" if platform == "android"
             else "MOBILE_IOS" if platform == "ios"
             else "BACKEND"
    ErrorReportingService.report_error(
        source=source,
        user=request.user,
        ...rest...
    )
    return self.success({"received": True}, status=201)

URLs: `src/api/urls/error_reporting.py`:
urlpatterns = [
    path("error-report/", ErrorReportCreateAPIView.as_view(),
         name="api_error_report_create"),
]

`src/api/urls/__init__.py` ga qo'sh:
path("", include("src.api.urls.error_reporting")),

### Settings o'zgarishlari

`config/settings/local.py`:
- TELEGRAM_BOT_TOKEN = env("TELEGRAM_BOT_TOKEN", default="")
- TELEGRAM_LOG_CHAT_ID = env("TELEGRAM_LOG_CHAT_ID", default="")
- TELEGRAM_NOTIFICATIONS_ENABLED = env.bool(
    "TELEGRAM_NOTIFICATIONS_ENABLED", default=False)
- REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"] ga "error_report": "30/min"
  qo'sh (mavjud "pin_verify" yonida)
- REST_FRAMEWORK["DEFAULT_THROTTLE_CLASSES"] tekshir — ScopedRateThrottle
  bormi, yo'q bo'lsa qo'sh
- LOGGING'ga handler va logger qo'sh (yuqorida ko'rsatilgan)

`config/settings/prod.py` — bu fayl local'dan import qiladi, lekin
TELEGRAM_NOTIFICATIONS_ENABLED default productionda True bo'lishi tabiiy.
Hozir o'zgartirma — bu env orqali sozlanadi.

`.env.dev` ga qo'shiladigan kalitlar (placeholder bilan):
TELEGRAM_BOT_TOKEN=
TELEGRAM_LOG_CHAT_ID=
TELEGRAM_NOTIFICATIONS_ENABLED=False

Agar `.env.example` mavjud emas, foydalanuvchidan so'ra: yaratamizmi?

### Tests

`tests/test_error_reporting.py` (yangi fayl, mavjud `tests/test_*.py`
pattern'iga moslab):

import qil:
- pytest, freezegun bo'lsa freezegun, aks holda Django timezone mock
- ErrorReport model
- ErrorReportingService
- TelegramNotifier
- requests_mock yoki mocker.patch — Telegram API mock qilish uchun

Testlar:

1. test_report_error_creates_new_record — yangi error, DB'da yozuv
2. test_report_error_duplicate_increments_count — ikkinchi marta
   chaqirilsa, count=2, faqat bitta row
3. test_fingerprint_differs_by_path — bir xil error_type, lekin har
   xil request_path → ikkita row
4. test_fingerprint_differs_by_status — bir xil path, lekin har xil
   status_code → ikkita row
5. test_first_occurrence_notifies — count=1 da TelegramNotifier.send
   bir marta chaqiriladi (mock bilan tekshir)
6. test_milestone_notifies — count 10 ga yetganda yana yuboriladi
7. test_non_milestone_skips — count=5 da yuborilmaydi
8. test_critical_always_notifies — severity=CRITICAL har doim
9. test_rate_limit_within_5_minutes — bir xil fingerprint 5 daqiqada
   2-marta chaqirilsa, faqat birinchisi TG'ga yuboradi
10. test_telegram_disabled_no_send — TELEGRAM_NOTIFICATIONS_ENABLED=False
    bo'lsa send chaqirilmaydi (DB hali yoziladi)
11. test_telegram_network_error_does_not_raise — requests.post
    ConnectionError tashlasa, report_error normal qaytadi
12. test_logging_handler_writes_report — Python logger.error()
    chaqirilsa, ErrorReport DB'da paydo bo'ladi
13. test_logging_handler_skips_own_recursion — agar logger
    "src.services.error_reporting"'dan bo'lsa, skip
14. test_api_unauthenticated_returns_401 — anonim user → 401
15. test_api_authenticated_creates_report — authenticated POST → 201
    + DB'da row + user FK to'g'ri
16. test_api_rate_limit_30_per_minute — 31-marta POST → 429
17. test_api_platform_android_sets_correct_source — platform=android →
    source=MOBILE_ANDROID
18. test_api_platform_ios_sets_correct_source — platform=ios →
    source=MOBILE_IOS

Test fixture'lar (`tests/conftest.py` da mavjud bo'lsa undan foydalan):
- authenticated_client (owner, phone_seller, accessory_seller)
- branch, user fixtures

### Migration

python manage.py makemigrations core
- Bitta fayl yaratiladi: 0XXX_errorreport.py
- O'qib chiqamiz va tasdiqlaymiz — destructive emas, faqat AddField
  va CreateModel bo'lishi kerak
- python manage.py migrate

### Yakuniy hisobot

Ish tugagandan keyin foydalanuvchiga ko'rsat:

1. Yaratilgan fayllar ro'yxati (8-10 ta fayl atrofida bo'lishi kerak)
2. O'zgartirilgan fayllar ro'yxati (kichik o'zgarishlar: settings,
   models/__init__, urls/__init__, .env.dev)
3. Migration nomi
4. `pytest tests/test_error_reporting.py -v` natijasi — barcha 18 test
   yashil bo'lishi shart
5. `pytest tests/ -x --tb=short` natijasi — mavjud testlar buzilmaganini
   ko'rsatish uchun
6. Foydalanuvchi qanday qilib qo'lda test qilish:
   - .env.dev ga real token va chat_id qo'shish
   - TELEGRAM_NOTIFICATIONS_ENABLED=True
   - python manage.py shell ichida:
     from src.services.error_reporting import ErrorReportingService
     ErrorReportingService.report_error(
         source="BACKEND",
         error_type="ManualTest",
         error_message="Hello from Mobirex backend",
         severity="ERROR",
     )
   - TG kanalga xabar kelishini ko'rish

### Eslatma

- Hech qanday mavjud test sinishi mumkin emas. Sinsa — fix sening
  noto'g'ri yondashuvingni bildiradi
- Hech qanday mavjud endpoint javob shakli o'zgarmaydi
- Mobile app hozir bu endpointni chaqirmaydi — mobile tomonidagi
  integratsiya keyingi alohida task
- `requests` paketi `requirements.txt` da mavjud bo'lishi kerak (Django
  bilan birga keladi yoki tekshir). Yo'q bo'lsa, foydalanuvchidan so'ra
  qo'shamizmi

Boshla 1-bosqichdan: AUDIT.

