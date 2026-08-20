import os
import environ
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
env = environ.Env()
environ.Env.read_env(os.path.join(BASE_DIR, '.env.dev'))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")

try:
    from celery import Celery
except ImportError:  # pragma: no cover
    celery_app = None
else:
    celery_app = Celery("config")
    celery_app.config_from_object("django.conf:settings", namespace="CELERY")
    celery_app.autodiscover_tasks()

__all__ = ["celery_app"]
