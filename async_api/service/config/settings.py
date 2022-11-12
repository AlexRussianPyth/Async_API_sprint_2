import os
from pathlib import Path

from split_settings.tools import include


# Определяем корневую папку проекта
BASE_DIR = Path(__file__).resolve().parent.parent

# Получаем секретный ключ и определяем, в каком режиме запустить проект
SECRET_KEY = os.environ.get("SECRET_KEY")
DEBUG = True if os.environ.get("DEBUG", False) == "True" else False

if not DEBUG:
    ALLOWED_HOSTS = os.environ.get("DJANGO_ALLOWED_HOSTS").split(" ")

INSTALLED_APPS = [
    'django.contrib.admin',
    'debug_toolbar',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'movies.apps.MoviesConfig',
    'corsheaders'
]

# Middleware Settings
include(
    'components/middleware.py',
)

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

CORS_ALLOWED_ORIGINS = ["http://127.0.0.1:8080"]

WSGI_APPLICATION = 'config.wsgi.application'

# Database Settings
include(
    'components/database.py',
)

# Passwords
include(
    'components/passwords.py',
)

# Internationalization
include(
    'components/internalization.py',
)

# Status Files and media
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

INTERNAL_IPS = [
    "127.0.0.1",
]

# Sentry
#include(
#    'components/sentry.py',
#)


# Loggining
#include(
#    'components/logger.py',
#)
