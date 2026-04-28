"""
Django settings for Lakshmi Crackers backend.
Migrated from MongoDB (djongo) to PostgreSQL (psycopg2).

Key changes:
  • Django upgraded from 3.2 → 4.2 LTS (djongo required 3.2; no longer needed)
  • DATABASE engine changed from djongo → django.db.backends.postgresql
  • DEFAULT_AUTO_FIELD changed to BigAutoField (Django 4.x default)
  • USE_L10N removed (deprecated in Django 4.x, now always True)
"""
from pathlib import Path
from datetime import timedelta
import os

BASE_DIR = Path(__file__).resolve().parent.parent

try:
    from dotenv import load_dotenv
    load_dotenv(BASE_DIR / '.env')
except ImportError:
    pass

# ─── Security ─────────────────────────────────────────────────────────────────
SECRET_KEY    = os.environ.get('SECRET_KEY', 'lakshmi-crackers-dev-secret-key-change-in-prod')
DEBUG         = os.environ.get('DEBUG', 'True') == 'True'
# Render sets RENDER_EXTERNAL_HOSTNAME automatically
_render_host = os.environ.get('RENDER_EXTERNAL_HOSTNAME', '')
_allowed     = os.environ.get('ALLOWED_HOSTS', '*')
ALLOWED_HOSTS = list(filter(None, _allowed.split(',') + ([_render_host] if _render_host else [])))

# ─── Applications ─────────────────────────────────────────────────────────────
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third-party
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',

    # Cloud storage
    'cloudinary_storage',
    'cloudinary',

    # Local apps
    'products',
    'orders',
    'users',
    'core',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # serve static files on Render
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF      = 'lakshmi_crackers.urls'
WSGI_APPLICATION  = 'lakshmi_crackers.wsgi.application'

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

# ─── Database — PostgreSQL ────────────────────────────────────────────────────
DATABASES = {
    'default': {
        'ENGINE':   'django.db.backends.postgresql',
        'NAME':     os.environ.get('POSTGRES_DB',       'lakshmi_crackers_db'),
        'USER':     os.environ.get('POSTGRES_USER',     'postgres'),
        'PASSWORD': os.environ.get('POSTGRES_PASSWORD', 'postgres'),
        'HOST':     os.environ.get('POSTGRES_HOST',     'localhost'),
        'PORT':     os.environ.get('POSTGRES_PORT',     '5432'),
        'OPTIONS': {
            'connect_timeout': 10,
        },
        'CONN_MAX_AGE': 60,  # Keep connections alive 60s (good for production)
    }
}

# ─── Auto primary key ─────────────────────────────────────────────────────────
# BigAutoField is Django 4.x default and best practice for PostgreSQL
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ─── Custom user model ────────────────────────────────────────────────────────
AUTH_USER_MODEL = 'users.User'

# ─── REST Framework ───────────────────────────────────────────────────────────
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticatedOrReadOnly',
    ),
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'EXCEPTION_HANDLER': 'core.exceptions.custom_exception_handler',
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon':            '100/hour',
        'user':            '1000/hour',
        'login':           '10/minute',
        'order_place':     '20/hour',
        'coupon_validate': '30/hour',
    },
}

# ─── JWT ──────────────────────────────────────────────────────────────────────
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME':  timedelta(hours=8),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS':  True,
    'AUTH_HEADER_TYPES':      ('Bearer',),
}

# ─── CORS ─────────────────────────────────────────────────────────────────────
CORS_ALLOW_ALL_ORIGINS = True   # Tighten in production
CORS_ALLOW_CREDENTIALS = True

# ─── Static & Media ───────────────────────────────────────────────────────────
STATIC_URL   = '/static/'
STATIC_ROOT  = BASE_DIR / 'staticfiles'
# WhiteNoise — serve compressed static files efficiently on Render
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
MEDIA_URL   = '/media/'
MEDIA_ROOT  = BASE_DIR / 'media'

# ─── Cloudinary — cloud image storage ────────────────────────────────────────
# Images are uploaded to Cloudinary instead of local disk.
# This survives Render restarts, redeploys, and ephemeral filesystem wipes.
# Set CLOUDINARY_URL in Render environment variables.
# Format: cloudinary://API_KEY:API_SECRET@CLOUD_NAME
# Get free credentials at https://cloudinary.com (25 GB free)
CLOUDINARY_URL = os.environ.get('CLOUDINARY_URL', '')

if CLOUDINARY_URL:
    # Use Cloudinary for all uploaded media files
    DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage'
    import cloudinary
    import urllib.parse
    _parsed = urllib.parse.urlparse(CLOUDINARY_URL)
    cloudinary.config(
        cloud_name = _parsed.hostname,
        api_key    = _parsed.username,
        api_secret = _parsed.password,
        secure     = True,
    )
else:
    # Fallback: local disk (dev only — not reliable on Render free tier)
    DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'

# ─── Email ────────────────────────────────────────────────────────────────────
# ─── Email — Gmail SMTP ─────────────────────────────────────────────────────
# Required Render environment variables:
#   EMAIL_HOST_USER     = lakshmicrackersonline@gmail.com
#   EMAIL_HOST_PASSWORD = your-16-char-gmail-app-password
# Optional (defaults already set for Gmail):
#   EMAIL_HOST     = smtp.gmail.com
#   EMAIL_PORT     = 587
#   EMAIL_USE_TLS  = True

EMAIL_HOST_USER     = os.environ.get('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')
EMAIL_HOST          = os.environ.get('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT          = int(os.environ.get('EMAIL_PORT', '587'))
EMAIL_USE_TLS       = os.environ.get('EMAIL_USE_TLS', 'True').strip().lower() == 'true'
EMAIL_USE_SSL       = False  # TLS and SSL are mutually exclusive — use TLS on port 587

# Always use SMTP in production — console backend is only for local dev
if EMAIL_HOST_USER and EMAIL_HOST_PASSWORD:
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
else:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

DEFAULT_FROM_EMAIL = EMAIL_HOST_USER or 'lakshmicrackersonline@gmail.com'
SERVER_EMAIL       = DEFAULT_FROM_EMAIL

# ─── Localisation ─────────────────────────────────────────────────────────────
LANGUAGE_CODE = 'en-us'
TIME_ZONE     = 'Asia/Kolkata'
USE_I18N      = True
USE_TZ        = True
# USE_L10N removed — deprecated in Django 4.x (always True now)

# ─── Password validation ──────────────────────────────────────────────────────
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
     'OPTIONS': {'min_length': 8}},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ─── Logging ──────────────────────────────────────────────────────────────────
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {'format': '[{asctime}] {levelname} {name} {message}', 'style': '{'},
    },
    'handlers': {
        'console': {'class': 'logging.StreamHandler', 'formatter': 'verbose'},
    },
    'root': {'handlers': ['console'], 'level': 'INFO'},
    'loggers': {
        'django':         {'handlers': ['console'], 'level': os.environ.get('DJANGO_LOG_LEVEL', 'INFO'), 'propagate': False},
        'django.request': {'handlers': ['console'], 'level': 'WARNING', 'propagate': False},
        'products':       {'handlers': ['console'], 'level': 'INFO', 'propagate': False},
        'orders':         {'handlers': ['console'], 'level': 'INFO', 'propagate': False},
        'users':          {'handlers': ['console'], 'level': 'INFO', 'propagate': False},
        'core':           {'handlers': ['console'], 'level': 'INFO', 'propagate': False},
    },
}
