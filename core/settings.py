"""
Django settings for Kanzen Labs project.
Final production-ready configuration with modular app support and custom auth.
"""

import os
from pathlib import Path
from datetime import timedelta

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# ──────────────────────────────────────────────────────────────────────
# SECURITY CONFIGURATION
# ──────────────────────────────────────────────────────────────────────

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-uj-unsd$u#h^_$96z_3%a@^*h7o3cv7f_u9^$yg%mc42af6&5k'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['*']


# ──────────────────────────────────────────────────────────────────────
# APPLICATION DEFINITION
# ──────────────────────────────────────────────────────────────────────

INSTALLED_APPS = [
    # Default Django Apps
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Third-party Packages
    'rest_framework',
    'corsheaders',
    "drf_spectacular",
    "drf_spectacular_sidecar",

    # Local Project Apps (Modular Architecture)
    'apps.users',
    'apps.products',
    # 'apps.compliance',
    # 'apps.ai_engine',
    # 'apps.logistics',
    # 'apps.meetings',
    # 'apps.growth',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware', # Enable CORS for frontend integration
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'core.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'core.wsgi.application'


# ──────────────────────────────────────────────────────────────────────
# AUTHENTICATION & USER MANAGEMENT
# ──────────────────────────────────────────────────────────────────────

# Point to our custom User model to avoid system check conflicts (E304)
AUTH_USER_MODEL = 'users.User'

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}


SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'BLACKLIST_AFTER_ROTATION': True,
    'AUTH_HEADER_TYPES': ('Bearer',),
}

SPECTACULAR_SETTINGS = {
    "TITLE": "Kanzen Labs API",
    "DESCRIPTION": "AI-powered cosmetic platform APIs",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
}
# ──────────────────────────────────────────────────────────────────────
# DATABASE CONFIGURATION
# ──────────────────────────────────────────────────────────────────────

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# ──────────────────────────────────────────────────────────────────────
# MEDIA & STATIC FILES
# ──────────────────────────────────────────────────────────────────────

STATIC_URL = 'static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Media files for Logo and Product image uploads
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')


# ──────────────────────────────────────────────────────────────────────
# INTERNATIONALIZATION & DEFAULTS
# ──────────────────────────────────────────────────────────────────────

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# CORS Settings (Allowing all for local development)
CORS_ALLOW_ALL_ORIGINS = True




EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# # settings.py (শুধুমাত্র যখন আসল ইমেইল পাঠাতে চাইবেন)
# EMAIL_HOST = 'smtp.gmail.com'
# EMAIL_PORT = 587
# EMAIL_USE_TLS = True
# EMAIL_HOST_USER = 'your-email@gmail.com'
# EMAIL_HOST_PASSWORD = 'your-app-password'


# settings.py
CORS_ALLOW_HEADERS = [
    "accept",
    "accept-encoding",
    "authorization", # এই লাইনটি থাকা বাধ্যতামূলক
    "content-type",
    "dnt",
    "origin",
    "user-agent",
    "x-csrftoken",
    "x-requested-with",
]