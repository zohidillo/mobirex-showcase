"""
ASGI config for config project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""

import os
import environ
from pathlib import Path
from django.core.asgi import get_asgi_application

BASE_DIR = Path(__file__).resolve().parent.parent
env = environ.Env()

env_file = os.path.join(BASE_DIR, '.env.dev')
if os.path.exists(env_file):
    environ.Env.read_env(env_file)

os.environ.setdefault(
    'DJANGO_SETTINGS_MODULE',
    env('DJANGO_SETTINGS_MODULE', default='config.settings.local'),
)

application = get_asgi_application()
