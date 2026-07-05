import os
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/6.0/howto/deployment/checklist/

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get('DEBUG', 'True').lower() == 'true'

# SECURITY WARNING: keep the secret key used in production secret!
# Im Debug-Modus wird ein unsicherer Entwicklungs-Key genutzt, damit lokale
# Entwicklung ohne Setup funktioniert. In Produktion (DEBUG=False) MUSS
# DJANGO_SECRET_KEY gesetzt sein, sonst bricht der Start bewusst ab.
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY')
if not SECRET_KEY:
    if DEBUG:
        SECRET_KEY = 'django-insecure-dev-only-key-change-me'
    else:
        raise RuntimeError(
            'DJANGO_SECRET_KEY muss in Produktion (DEBUG=False) gesetzt sein.'
        )

# Erlaubte Hosts aus der Umgebung; im Debug-Modus lokal offen.
ALLOWED_HOSTS = [
    h.strip() for h in os.environ.get('DJANGO_ALLOWED_HOSTS', '').split(',') if h.strip()
]
if not ALLOWED_HOSTS:
    ALLOWED_HOSTS = ['localhost', '127.0.0.1'] if not DEBUG else ['*']

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'corsheaders',
    'ats',
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

ROOT_URLCONF = 'securats.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'ats.branding.branding_context_processor',
                'ats.context_processors.demo_flags',  # P0.4
            ],
        },
    },
]

WSGI_APPLICATION = 'securats.wsgi.application'

# Database
# https://docs.djangoproject.com/en/6.0/ref/settings/#databases

# Flexible SQLite path loading (supports .env configuration)
db_url = os.environ.get('DATABASE_URL', 'file:dev.db')
if db_url.startswith('file:'):
    db_path = db_url.split('file:')[-1]
    # Handle relative or absolute paths
    if not os.path.isabs(db_path):
        db_path = BASE_DIR / db_path
else:
    db_path = BASE_DIR / 'dev.db'

# WP7 — Ziel-DB-Entscheidung (NORTHSTAR offene Frage #3):
# PRODUKTION: PostgreSQL (Nebenläufigkeit ai_worker+Web, select_for_update/
# skip_locked, robuste Backups via pg_dump — Backup-Skripte setzen das voraus).
# ENTWICKLUNG/EVALUATION: SQLite (Null-Setup) bleibt Default.
# Aktivierung: POSTGRES_HOST (+ _DB/_USER/_PASSWORD/_PORT) in der Umgebung setzen.
if os.environ.get('POSTGRES_HOST'):
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'HOST': os.environ['POSTGRES_HOST'],
            'PORT': os.environ.get('POSTGRES_PORT', '5432'),
            'NAME': os.environ.get('POSTGRES_DB', 'securats'),
            'USER': os.environ.get('POSTGRES_USER', 'securats'),
            'PASSWORD': os.environ.get('POSTGRES_PASSWORD', ''),
            'CONN_MAX_AGE': 60,
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': db_path,
        }
    }

# Password validation
# https://docs.djangoproject.com/en/6.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
# https://docs.djangoproject.com/en/6.0/topics/i18n/

LANGUAGE_CODE = 'de-de'

TIME_ZONE = 'Europe/Berlin'

USE_I18N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/6.0/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# CORS & CSRF configurations
# WICHTIG: CORS_ALLOW_ALL_ORIGINS zusammen mit CORS_ALLOW_CREDENTIALS ist
# unsicher und wird von Browsern ohnehin abgelehnt. Stattdessen eine feste
# Allowlist (identisch zu den CSRF Trusted Origins) nutzen.
CORS_ALLOWED_ORIGINS = [
    o.strip() for o in os.environ.get('CORS_ALLOWED_ORIGINS', '').split(',') if o.strip()
] or [
    'http://localhost:3000',
    'http://127.0.0.1:3000',
    'http://localhost:8000',
    'http://127.0.0.1:8000',
    'http://localhost:3001',
    'http://127.0.0.1:3001',
]
CORS_ALLOW_CREDENTIALS = True
CSRF_TRUSTED_ORIGINS = CORS_ALLOWED_ORIGINS

# Zusaetzliche Sicherheits-Header/Cookies in Produktion aktivieren.
if not DEBUG:
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True

# Custom setting for PII Encryption Key.
# In Produktion (DEBUG=False) ist ein explizit gesetzter Schluessel Pflicht,
# damit nicht versehentlich mit dem oeffentlich bekannten Fallback verschluesselt wird.
PII_ENCRYPTION_KEY = os.environ.get('PII_ENCRYPTION_KEY')
if not PII_ENCRYPTION_KEY:
    if DEBUG:
        PII_ENCRYPTION_KEY = 'securats-fallback-super-secure-encryption-key-for-pii-at-rest='
    else:
        raise RuntimeError(
            'PII_ENCRYPTION_KEY muss in Produktion (DEBUG=False) gesetzt sein.'
        )

# --- Authentifizierung / RBAC (Phase 2) ---
# Login-Seite für @login_required / role_required.
LOGIN_URL = "ats:login"
LOGIN_REDIRECT_URL = "ats:dashboard"
LOGOUT_REDIRECT_URL = "ats:home"

# WP2/UC-NS-06: Optionales Zugriffstoken für die öffentlichen Job-Feeds.
# Wenn gesetzt, müssen Feed-Requests ?token=... oder Header X-Feed-Token liefern.
# Leer = offen (bestehende Syndication bleibt funktionsfähig); für KRITIS-Betrieb setzen.
FEED_ACCESS_TOKEN = os.environ.get('FEED_ACCESS_TOKEN', '')

# P0.4: Demo-Instanz (Banner + Freigabe fuer seed_demo --reset)
DEMO_MODE = os.environ.get('DEMO_MODE', '') == '1'
