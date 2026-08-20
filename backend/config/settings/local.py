from datetime import timedelta

import environ
from config.settings.base import *

BASE_DIR = BASE_DIR.parent
env = environ.Env()
environ.Env.read_env(os.path.join(BASE_DIR, ".env.dev"))

DEBUG = True

ALLOWED_HOSTS = ["*"]

# ========================
# DATABASE
# ========================

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "crm_db",
        "USER": "server",
        "PASSWORD": "123",
        "HOST": "127.0.0.1",
        "PORT": "5432",
    }
}

# ========================
# CUSTOM USER MODEL
# ========================

AUTH_USER_MODEL = "core.CustomUser"
AUTHENTICATION_BACKENDS = [
    "axes.backends.AxesStandaloneBackend",
    "django.contrib.auth.backends.ModelBackend",
]

# ========================
# INSTALLED APPS
# ========================

INSTALLED_APPS += [
    "src.core",
    "rest_framework",
    "drf_spectacular",
    "rest_framework_simplejwt.token_blacklist",
    "axes",
    "corsheaders",
]

MIDDLEWARE += [
    "axes.middleware.AxesMiddleware",
]

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_PAGINATION_CLASS": "src.api.pagination.StandardPagination",
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": "60/min",
        "user": "300/min",
        "pin_verify": "10/min",
        "error_report": "30/min",
        "login": "10/min",
        "landing_form": "5/hour",
        "public_contact_hour": "3/hour",
        "public_contact_day": "10/day",
    },
    "EXCEPTION_HANDLER": "src.api.exception_handler.api_exception_handler",
    "PAGE_SIZE": 20,
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=5),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=1),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "AUTH_HEADER_TYPES": ("Bearer",),
    "AUTH_TOKEN_CLASSES": ("rest_framework_simplejwt.tokens.AccessToken",),
}

SPECTACULAR_SETTINGS = {
    "TITLE": "API Documentation",
    "DESCRIPTION": "Backend API for system",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
}

# ========================
# LOGIN / LOGOUT
# ========================

LOGIN_URL = "/"
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/"

# ========================
# TEMPLATES
# ========================

TEMPLATES[0]["DIRS"] = [
    BASE_DIR / "templates",
]

# ========================
# STATIC FILES
# ========================

STATIC_URL = "/static/"

STATICFILES_DIRS = [
    BASE_DIR / "static",
]

STATIC_ROOT = BASE_DIR / "staticfiles"

# ========================
# MEDIA FILES
# ========================

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"
# ========================
# TIMEZONE
# ========================

TIME_ZONE = "Asia/Tashkent"

USE_TZ = True

# ========================
# CORS (local dev — barcha origin)
# ========================

CORS_ALLOW_ALL_ORIGINS = True

SUPPORT_REQUEST_X_KEY = env("SUPPORT_REQUEST_X_KEY", default="")

TELEGRAM_BOT_TOKEN = env("TELEGRAM_BOT_TOKEN", default="")
TELEGRAM_LOG_CHAT_ID = env("TELEGRAM_LOG_CHAT_ID", default="")
TELEGRAM_NOTIFICATIONS_ENABLED = env.bool("TELEGRAM_NOTIFICATIONS_ENABLED", default=False)

# Support guruhi xato-kanalidan boshqa bot bo‘lishi mumkin. Alohida token
# berilmasa, TELEGRAM_BOT_TOKEN ishlatiladi — u holda o‘sha bot guruhga
# a’zo bo‘lishi shart, aks holda Telegram 403 qaytaradi.
TELEGRAM_SUPPORT_BOT_TOKEN = env("TELEGRAM_SUPPORT_BOT_TOKEN", default="")
TELEGRAM_SUPPORT_CHAT_ID = env("TELEGRAM_SUPPORT_CHAT_ID", default="")

# Telegram xabaridagi "CRM’da ochish" havolasi uchun. Bo‘sh bo‘lsa havola
# qo‘shilmaydi.
CRM_BASE_URL = env("CRM_BASE_URL", default="")

# ========================
# DEFAULT AUTO FIELD
# ========================

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ========================
# MESSAGE STORAGE
# ========================

MESSAGE_STORAGE = "django.contrib.messages.storage.session.SessionStorage"

# ========================
# SESSION
# ========================

SESSION_COOKIE_AGE = 60 * 60 * 24 * 30  # 30 days

SESSION_SAVE_EVERY_REQUEST = True

# ========================
# BRUTE-FORCE HIMOYASI
# ========================

AXES_FAILURE_LIMIT = 5
AXES_COOLOFF_TIME = 1
AXES_LOCK_OUT_AT_FAILURE = True
AXES_RESET_ON_SUCCESS = True
AXES_LOCKOUT_PARAMETERS = [["ip_address", "username"]]

# ========================
# DEBUG TOOLBAR
# ========================

try:
    import debug_toolbar  # noqa: F401

    DEBUG_TOOLBAR_AVAILABLE = True
except Exception as e:
    DEBUG_TOOLBAR_AVAILABLE = False

if DEBUG and DEBUG_TOOLBAR_AVAILABLE:
    INSTALLED_APPS += ["debug_toolbar"]
    MIDDLEWARE += ["debug_toolbar.middleware.DebugToolbarMiddleware"]
    INTERNAL_IPS = ["127.0.0.1"]

try:
    from celery.schedules import crontab
except ImportError:  # pragma: no cover
    crontab = None

CELERY_BROKER_URL = env(
    "CELERY_BROKER_URL",
    default=f"redis://{env('REDIS_HOST', default='127.0.0.1')}:{env('REDIS_PORT', default='6379')}/0",
)
CELERY_RESULT_BACKEND = env("CELERY_RESULT_BACKEND", default=CELERY_BROKER_URL)
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = TIME_ZONE
CELERY_ENABLE_UTC = False

if crontab:
    CELERY_BEAT_SCHEDULE = {
        "daily-charge-all-users": {
            "task": "src.core.tasks.billing.run_daily_charges",
            "schedule": crontab(minute=0, hour=1),
        },
        "monthly-close-all-branches": {
            "task": "src.core.tasks.month_closing.run_month_close_task",
            "schedule": crontab(minute=0, hour=0, day_of_month=1),
        }
    }
else:  # pragma: no cover
    CELERY_BEAT_SCHEDULE = {}

LOGGING["formatters"] = {
    **LOGGING.get("formatters", {}),
    "month_closing_verbose": {
        "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    },
    "verbose": {
        "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    },
}
LOGGING["handlers"] = {
    **LOGGING.get("handlers", {}),
    "month_closing_file": {
        "class": "logging.handlers.RotatingFileHandler",
        "filename": str(BASE_DIR / "month_closing.log"),
        "maxBytes": 5 * 1024 * 1024,
        "backupCount": 5,
        "formatter": "month_closing_verbose",
    },
    "telegram": {
        "class": "src.services.error_reporting.logging_handler.TelegramLoggingHandler",
        "level": "ERROR",
        "formatter": "verbose",
    },
}
LOGGING["loggers"] = {
    **LOGGING.get("loggers", {}),
    "billing": {
        "handlers": ["console", "telegram"],
        "level": "INFO",
        "propagate": False,
    },
    "month_closing": {
        "handlers": ["console", "month_closing_file", "telegram"],
        "level": "INFO",
        "propagate": False,
    },
    "django.request": {
        "handlers": ["telegram"],
        "level": "ERROR",
        "propagate": True,
    },
    "celery.task": {
        "handlers": ["console", "telegram"],
        "level": "ERROR",
        "propagate": False,
    },
    "celery.worker": {
        "handlers": ["console", "telegram"],
        "level": "ERROR",
        "propagate": False,
    },
}
