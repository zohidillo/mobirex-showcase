"""
WSGI config for config project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/wsgi/
"""

import os
import environ
from pathlib import Path
from django.core.wsgi import get_wsgi_application

BASE_DIR = Path(__file__).resolve().parent.parent
env = environ.Env()

env_file = os.path.join(BASE_DIR, '.env.dev')
if os.path.exists(env_file):
    environ.Env.read_env(env_file)

os.environ.setdefault(
    'DJANGO_SETTINGS_MODULE',
    env('DJANGO_SETTINGS_MODULE', default='config.settings.local'),
)

application = get_wsgi_application()
