from datetime import timedelta

import environ
from django.core.exceptions import ImproperlyConfigured

from config.settings.base import *  # noqa: F401, F403

BASE_DIR = BASE_DIR.parent
env = environ.Env()

# ========================
# CORE SECURITY
# ========================

DEBUG = env.bool("DEBUG", default=False)
SECRET_KEY = env("SECRET_KEY")

if len(SECRET_KEY) < 50:
    raise ImproperlyConfigured(
        "SECRET_KEY production'da kamida 50 belgi bo'lishi shart"
    )

ALLOWED_HOSTS = env.list("ALLOWED_HOSTS")

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

# ========================
# MIDDLEWARE (axes ENG OXIRIDA)
# ========================

MIDDLEWARE += [
    "axes.middleware.AxesMiddleware",
]

# ========================
# DATABASE
# ========================

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": env("DB_NAME", default="crm_db"),
        "USER": env("DB_USER", default="crm_user"),
        "PASSWORD": env("DB_PASSWORD", default="crm_pass"),
        "HOST": env("DB_HOST", default="db"),
        "PORT": env("DB_PORT", default="5432"),
    }
}

# ========================
# CACHES (REDIS)
# ========================

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": f"redis://{env('REDIS_HOST', default='redis')}:{env('REDIS_PORT', default='6379')}/1",
    }
}

# ========================
# REST FRAMEWORK
# ========================

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

# ========================
# SIMPLE JWT
# ========================

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=5),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=1),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "AUTH_HEADER_TYPES": ("Bearer",),
    "AUTH_TOKEN_CLASSES": ("rest_framework_simplejwt.tokens.AccessToken",),
}

# ========================
# API DOCS
# ========================

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

STATIC_ROOT = "/app/staticfiles"

# ========================
# MEDIA FILES
# ========================

MEDIA_URL = "/media/"
MEDIA_ROOT = "/app/media"

# ========================
# TIMEZONE
# ========================

TIME_ZONE = "Asia/Tashkent"
USE_TZ = True

# ========================
# SESSION & MESSAGES
# ========================

MESSAGE_STORAGE = "django.contrib.messages.storage.session.SessionStorage"
SESSION_COOKIE_AGE = 60 * 60 * 24 * 30  # 30 kun
SESSION_SAVE_EVERY_REQUEST = True

# ========================
# SECURITY HEADERS
# ========================

CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True
CSRF_TRUSTED_ORIGINS = [
    "https://crm.b26.uz",
    "https://mobirex.uz",
    "https://www.mobirex.uz",
    "https://api.mobirex.uz",
]

# ========================
# CORS
# ========================

CORS_ALLOWED_ORIGINS = [
    "https://mobirex.uz",
    "https://www.mobirex.uz",
]
CORS_ALLOW_CREDENTIALS = False
CORS_ALLOW_METHODS = ["GET", "POST", "OPTIONS"]
CORS_ALLOW_HEADERS = [
    "accept",
    "accept-encoding",
    "authorization",
    "content-type",
    "dnt",
    "origin",
    "user-agent",
    "x-csrftoken",
    "x-requested-with",
    "x-key",
]

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"
SECURE_REFERRER_POLICY = "same-origin"

# ========================
# BRUTE-FORCE HIMOYASI
# ========================

AXES_FAILURE_LIMIT = 5
AXES_COOLOFF_TIME = 1  # 1 soat ban
AXES_LOCK_OUT_AT_FAILURE = True
AXES_RESET_ON_SUCCESS = True
AXES_LOCKOUT_PARAMETERS = [["ip_address", "username"]]

# ========================
# TELEGRAM / ERROR REPORTING
# ========================

SUPPORT_REQUEST_X_KEY = env("SUPPORT_REQUEST_X_KEY", default="")

TELEGRAM_BOT_TOKEN = env("TELEGRAM_BOT_TOKEN", default="")
TELEGRAM_LOG_CHAT_ID = env("TELEGRAM_LOG_CHAT_ID", default="")
TELEGRAM_NOTIFICATIONS_ENABLED = env.bool("TELEGRAM_NOTIFICATIONS_ENABLED", default=True)

# Support guruhi xato-kanalidan boshqa bot bo‘lishi mumkin. Alohida token
# berilmasa, TELEGRAM_BOT_TOKEN ishlatiladi — u holda o‘sha bot guruhga
# a’zo bo‘lishi shart, aks holda Telegram 403 qaytaradi.
TELEGRAM_SUPPORT_BOT_TOKEN = env("TELEGRAM_SUPPORT_BOT_TOKEN", default="")
TELEGRAM_SUPPORT_CHAT_ID = env("TELEGRAM_SUPPORT_CHAT_ID", default="")

# Telegram xabaridagi "CRM’da ochish" havolasi uchun. Bo‘sh bo‘lsa havola
# qo‘shilmaydi.
CRM_BASE_URL = env("CRM_BASE_URL", default="")

# ========================
# CELERY
# ========================

try:
    from celery.schedules import crontab
except ImportError:
    crontab = None

CELERY_BROKER_URL = env(
    "CELERY_BROKER_URL",
    default=f"redis://{env('REDIS_HOST', default='redis')}:{env('REDIS_PORT', default='6379')}/0",
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
        },
    }
else:
    CELERY_BEAT_SCHEDULE = {}

# ========================
# LOGGING
# ========================

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
