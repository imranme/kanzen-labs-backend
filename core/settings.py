import os
from pathlib import Path
from datetime import timedelta
import environ

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Initialize environment variables
env = environ.Env()

# Force Django to search exactly in your main project folder
env_file_path = os.path.join(BASE_DIR, '.env')

if os.path.exists(env_file_path):
    environ.Env.read_env(env_file_path)
else:
    print(f"CRITICAL WARNING: .env file not found at {env_file_path}")

# ──────────────────────────────────────────────────────────────────────
# SECURITY CONFIGURATION
# ──────────────────────────────────────────────────────────────────────

SECRET_KEY = 'django-insecure-uj-unsd$u#h^_$96z_3%a@^*h7o3cv7f_u9^$yg%mc42af6&5k'

DEBUG = True

ALLOWED_HOSTS = [
    "particularistically-transelementary-owen.ngrok-free.dev",
    "localhost",
    "127.0.0.1",
    "*", 
]


# ──────────────────────────────────────────────────────────────────────
# APPLICATION DEFINITION
# ──────────────────────────────────────────────────────────────────────

INSTALLED_APPS = [
    "unfold", 
    "unfold.contrib.filters",
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
    'apps.compliance',
    'apps.logistics',
    'apps.ai_engine',
    'apps.growth',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware', 
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


# ──────────────────────────────────────────────────────────────────────
# SECURITY & CORS CONFIGURATION
# ──────────────────────────────────────────────────────────────────────

CORS_ALLOW_ALL_ORIGINS = True

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
]

CSRF_TRUSTED_ORIGINS = [
    "https://particularistically-transelementary-owen.ngrok-free.dev",
]


# ──────────────────────────────────────────────────────────────────────
# SMTP EMAIL CONFIGURATION (PROD / HOSTINGER)
# ──────────────────────────────────────────────────────────────────────

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = env("EMAIL_HOST")

EMAIL_PORT = 587           
EMAIL_USE_TLS = True       
EMAIL_USE_SSL = False     

EMAIL_HOST_USER = env("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD")
DEFAULT_FROM_EMAIL = f"Acxess Team <{EMAIL_HOST_USER}>"

# # settings.py এর SMTP সেকশনের নিচে সাময়িকভাবে যোগ করুন
# print(f"SMTP USER: {EMAIL_HOST_USER}")
# print(f"SMTP PASSWORD: {EMAIL_HOST_PASSWORD}")
# ──────────────────────────────────────────────────────────────────────
# UNFOLD ADMIN SETTINGS
# ──────────────────────────────────────────────────────────────────────

UNFOLD_MAIN_SETTINGS = {
    "SITE_TITLE": "Kanzen Labs Administration",
    "SITE_HEADER": "Kanzen Labs Admin",
    "SITE_SYMBOL": "bi-beauty", 
    "SHOW_HISTORY": True,
    "SHOW_VIEW_ON_SITE": True,
    
    "SIDEBAR": {
        "show_search": True,
        "navigation": [
            {
                "title": "User Management",
                "separator": True,
                "items": [
                    {
                        "title": "Users",
                        "icon": "people",
                        "link": "admin:users_user_changelist",
                    },
                    {
                        "title": "Partner Profiles",
                        "icon": "badge_status",
                        "link": "admin:users_partnerprofile_changelist",
                    },
                ],
            },
            {
                "title": "Products & Logistics",
                "separator": True,
                "items": [
                    {
                        "title": "Products",
                        "icon": "inventory_2",
                        "link": "admin:products_product_changelist",
                    },
                    {
                        "title": "Batch Records",
                        "icon": "layers",
                        "link": "admin:products_batchrecord_changelist",
                    },
                    {
                        "title": "Logistics Docs",
                        "icon": "description",
                        "link": "admin:logistics_generatedlogisticdoc_changelist",
                    },
                ],
            },
            {
                "title": "Growth & AI Analytics",
                "separator": True,
                "items": [
                    {
                        "title": "Chemist Chats",
                        "icon": "chat",
                        "link": "admin:ai_engine_chemistchatsession_changelist",
                    },
                    {
                        "title": "Margin Calculations",
                        "icon": "payments",
                        "link": "admin:growth_margincalculation_changelist",
                    },
                    {
                        "title": "Forecast Records",
                        "icon": "trending_up",
                        "link": "admin:ai_engine_forecastrecord_changelist",
                    },
                ],
            },
            {
                "title": "Compliance Safety",
                "separator": True,
                "items": [
                    {
                        "title": "Compliance Documents",
                        "icon": "gavel",
                        "link": "admin:compliance_compliancedocument_changelist",
                    },
                ],
            },
        ],
    },
}