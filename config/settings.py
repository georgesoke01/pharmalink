# config/settings.py
# ─────────────────────────────────────────────────────────────────────────────
# Fichier de configuration unique — tout est piloté par le fichier .env
# Dev  : DEBUG=True  + SQLite  + outils debug
# Prod : DEBUG=False + PostgreSQL + Redis + Sentry + HTTPS
# ─────────────────────────────────────────────────────────────────────────────
from pathlib import Path
from datetime import timedelta
import os
import environ

# ── Chemins ───────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent

# ── Lecture du fichier .env ───────────────────────────────────────────────────
env = environ.Env(
    # (type, valeur_par_défaut)
    DEBUG                   = (bool,  False),
    ALLOWED_HOSTS           = (list,  ["127.0.0.1", "localhost"]),
    CORS_ALLOW_ALL_ORIGINS  = (bool,  False),
    CORS_ALLOWED_ORIGINS    = (list,  []),
    CORS_ALLOW_CREDENTIALS  = (bool,  False),
    USE_POSTGIS             = (bool,  False),   # False = SQLite/SpatiaLite en dev
    DB_NAME                 = (str,   "pharmalink"),
    DB_USER                 = (str,   "pharmalink"),
    DB_PASSWORD             = (str,   ""),
    DB_HOST                 = (str,   "db"),
    DB_PORT                 = (int,   5432),
    DB_CONN_MAX_AGE         = (int,   0),       # 0 = pas de persistance (dev), 600 en prod
    REDIS_URL               = (str,   "redis://redis:6379/0"),
    USE_REDIS_CACHE         = (bool,  False),   # False en dev, True en prod
    USE_HTTPS               = (bool,  False),   # False en dev, True en prod
    SENDGRID_API_KEY        = (str,   ""),
    DEFAULT_FROM_EMAIL      = (str,   "noreply@pharmalink.bj"),
    SENTRY_DSN              = (str,   ""),
    APP_VERSION             = (str,   "1.0.0"),
    USE_DEBUG_TOOLBAR       = (bool,  False),
    USE_DJANGO_EXTENSIONS   = (bool,  False),
)

environ.Env.read_env(BASE_DIR / ".env")   # charge le fichier .env à la racine du projet

# ─────────────────────────────────────────────────────────────────────────────
# 1. CORE
# ─────────────────────────────────────────────────────────────────────────────
SECRET_KEY   = env("DJANGO_SECRET_KEY")
DEBUG        = env("DEBUG")
ALLOWED_HOSTS = env("ALLOWED_HOSTS")

# ─────────────────────────────────────────────────────────────────────────────
# 2. APPLICATIONS
# ─────────────────────────────────────────────────────────────────────────────
# USE_POSTGIS contrôle l'activation de django.contrib.gis
# En dev Windows : USE_POSTGIS=False → pas de GDAL requis
USE_POSTGIS = env("USE_POSTGIS")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Third-party
    "rest_framework",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
    "corsheaders",
    "django_filters",
    "drf_spectacular",
    "celery",
    # Apps PharmaLink
    "apps.users",
    "apps.pharmacies",
    "apps.produits",
    "apps.horaires",
    "apps.gardes",
    "apps.connecteurs_lgo",
]

# GIS uniquement en production (nécessite GDAL + PostGIS)
if USE_POSTGIS:
    INSTALLED_APPS.insert(6, "django.contrib.gis")

# Outils de développement — activés uniquement si DEBUG + variables .env à True
if env("USE_DEBUG_TOOLBAR"):
    INSTALLED_APPS += ["debug_toolbar"]

if env("USE_DJANGO_EXTENSIONS"):
    INSTALLED_APPS += ["django_extensions"]

# ─────────────────────────────────────────────────────────────────────────────
# 3. MIDDLEWARE
# ─────────────────────────────────────────────────────────────────────────────
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

if env("USE_DEBUG_TOOLBAR"):
    MIDDLEWARE.insert(0, "debug_toolbar.middleware.DebugToolbarMiddleware")

# ─────────────────────────────────────────────────────────────────────────────
# 4. URLS / TEMPLATES / WSGI
# ─────────────────────────────────────────────────────────────────────────────
ROOT_URLCONF      = "config.urls"
WSGI_APPLICATION  = "config.wsgi.application"
AUTH_USER_MODEL   = "users.CustomUser"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

# ─────────────────────────────────────────────────────────────────────────────
# 5. BASE DE DONNÉES
# ─────────────────────────────────────────────────────────────────────────────
if USE_POSTGIS:
    # ── Production : PostgreSQL + PostGIS ─────────────────────────────────────
    DATABASES = {
        "default": {
            "ENGINE":       "django.contrib.gis.db.backends.postgis",
            "NAME":         env("DB_NAME"),
            "USER":         env("DB_USER"),
            "PASSWORD":     env("DB_PASSWORD"),
            "HOST":         env("DB_HOST"),
            "PORT":         env("DB_PORT"),
            "CONN_MAX_AGE": env("DB_CONN_MAX_AGE"),
            "OPTIONS": {
                "connect_timeout": 10,
                "options": "-c statement_timeout=30000",
            },
        }
    }
else:
    # ── Développement : SQLite standard (pas de GIS requis sur Windows) ─────────
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME":   BASE_DIR / "db.sqlite3",
        }
    }

# ─────────────────────────────────────────────────────────────────────────────
# 6. CACHE
# ─────────────────────────────────────────────────────────────────────────────
if env("USE_REDIS_CACHE"):
    # ── Production : Redis ────────────────────────────────────────────────────
    CACHES = {
        "default": {
            "BACKEND":  "django.core.cache.backends.redis.RedisCache",
            "LOCATION": env("REDIS_URL"),
            "OPTIONS":  {"CLIENT_CLASS": "django_redis.client.DefaultClient"},
            "KEY_PREFIX": "pharmalink",
            "TIMEOUT": 300,
        }
    }
    SESSION_ENGINE     = "django.contrib.sessions.backends.cache"
    SESSION_CACHE_ALIAS = "default"
else:
    # ── Développement : cache mémoire locale ──────────────────────────────────
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        }
    }

# ─────────────────────────────────────────────────────────────────────────────
# 7. INTERNATIONALISATION
# ─────────────────────────────────────────────────────────────────────────────
LANGUAGE_CODE = "fr-fr"
TIME_ZONE     = "Africa/Porto-Novo"
USE_I18N      = True
USE_TZ        = True

# ─────────────────────────────────────────────────────────────────────────────
# 8. STATIC & MEDIA
# ─────────────────────────────────────────────────────────────────────────────
STATIC_URL  = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_URL   = "/media/"
MEDIA_ROOT  = BASE_DIR / "media"

if not DEBUG:
    STATICFILES_STORAGE = "django.contrib.staticfiles.storage.ManifestStaticFilesStorage"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ─────────────────────────────────────────────────────────────────────────────
# 9. SÉCURITÉ HTTPS (production uniquement)
# ─────────────────────────────────────────────────────────────────────────────
if env("USE_HTTPS"):
    SECURE_HSTS_SECONDS           = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD           = True
    SECURE_SSL_REDIRECT           = True
    SECURE_PROXY_SSL_HEADER       = ("HTTP_X_FORWARDED_PROTO", "https")
    SECURE_CONTENT_TYPE_NOSNIFF   = True
    SECURE_BROWSER_XSS_FILTER     = True
    X_FRAME_OPTIONS               = "DENY"
    SESSION_COOKIE_SECURE         = True
    SESSION_COOKIE_HTTPONLY       = True
    SESSION_COOKIE_SAMESITE       = "Lax"
    CSRF_COOKIE_SECURE            = True
    CSRF_COOKIE_HTTPONLY          = True
    CSRF_COOKIE_SAMESITE          = "Lax"

# ─────────────────────────────────────────────────────────────────────────────
# 10. CORS
# ─────────────────────────────────────────────────────────────────────────────
if env("CORS_ALLOW_ALL_ORIGINS"):
    CORS_ALLOW_ALL_ORIGINS = True       # dev uniquement
else:
    CORS_ALLOWED_ORIGINS   = env("CORS_ALLOWED_ORIGINS")
    CORS_ALLOW_CREDENTIALS = env("CORS_ALLOW_CREDENTIALS")

# ─────────────────────────────────────────────────────────────────────────────
# 11. EMAIL
# ─────────────────────────────────────────────────────────────────────────────
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL")

if DEBUG:
    EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
else:
    EMAIL_BACKEND       = "django.core.mail.backends.smtp.EmailBackend"
    EMAIL_HOST          = "smtp.sendgrid.net"
    EMAIL_PORT          = 587
    EMAIL_USE_TLS       = True
    EMAIL_HOST_USER     = "apikey"
    EMAIL_HOST_PASSWORD = env("SENDGRID_API_KEY")
    SERVER_EMAIL        = DEFAULT_FROM_EMAIL

# ─────────────────────────────────────────────────────────────────────────────
# 12. DJANGO REST FRAMEWORK
# ─────────────────────────────────────────────────────────────────────────────
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ],
    "DEFAULT_PAGINATION_CLASS": "config.pagination.FlexiblePageNumberPagination",
    "PAGE_SIZE": 20,
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": "100/min",
        "user": "1000/min",
    },
}

# ─────────────────────────────────────────────────────────────────────────────
# 13. JWT
# ─────────────────────────────────────────────────────────────────────────────
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME":  timedelta(minutes=30),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS":  True,
    "BLACKLIST_AFTER_ROTATION": True,
    "AUTH_HEADER_TYPES": ("Bearer",),
}

# ─────────────────────────────────────────────────────────────────────────────
# 14. CELERY
# ─────────────────────────────────────────────────────────────────────────────
CELERY_BROKER_URL      = env("REDIS_URL")
CELERY_RESULT_BACKEND  = env("REDIS_URL")
CELERY_ACCEPT_CONTENT  = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE        = "Africa/Porto-Novo"

# ─────────────────────────────────────────────────────────────────────────────
# 15. LOGGING
# ─────────────────────────────────────────────────────────────────────────────
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format":  "[{asctime}] {levelname} {name} — {message}",
            "style":   "{",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    },
    "handlers": {
        "console": {
            "class":     "logging.StreamHandler",
            "formatter": "verbose",
        },
        "file_errors": {
            "class":       "logging.handlers.RotatingFileHandler",
            "filename":    BASE_DIR / "logs" / "errors.log",
            "maxBytes":    10 * 1024 * 1024,
            "backupCount": 5,
            "level":       "ERROR",
            "formatter":   "verbose",
        },
        "file_lgo": {
            "class":       "logging.handlers.RotatingFileHandler",
            "filename":    BASE_DIR / "logs" / "lgo_sync.log",
            "maxBytes":    5 * 1024 * 1024,
            "backupCount": 3,
            "formatter":   "verbose",
        },
    },
    "loggers": {
        "django": {
            "handlers":  ["console", "file_errors"],
            "level":     "DEBUG" if DEBUG else "INFO",
            "propagate": False,
        },
        "django.db.backends": {
            "handlers":  ["console"],
            "level":     "DEBUG" if DEBUG else "ERROR",  # SQL visible en dev, silencieux en prod
            "propagate": False,
        },
        "apps.connecteurs_lgo": {
            "handlers":  ["console", "file_lgo"],
            "level":     "INFO",
            "propagate": False,
        },
        "rest_framework": {
            "handlers":  ["console", "file_errors"],
            "level":     "WARNING",
            "propagate": False,
        },
    },
    "root": {
        "handlers": ["console"],
        "level":    "DEBUG" if DEBUG else "WARNING",
    },
}

# ─────────────────────────────────────────────────────────────────────────────
# 16. DEBUG TOOLBAR (dev uniquement)
# ─────────────────────────────────────────────────────────────────────────────
if env("USE_DEBUG_TOOLBAR"):
    INTERNAL_IPS = ["127.0.0.1", "localhost"]

    DEBUG_TOOLBAR_CONFIG = {
        "SHOW_TOOLBAR_CALLBACK": lambda request: DEBUG,
        "SHOW_COLLAPSED": True,
    }

    DEBUG_TOOLBAR_PANELS = [
        "debug_toolbar.panels.history.HistoryPanel",
        "debug_toolbar.panels.versions.VersionsPanel",
        "debug_toolbar.panels.timer.TimerPanel",
        "debug_toolbar.panels.settings.SettingsPanel",
        "debug_toolbar.panels.headers.HeadersPanel",
        "debug_toolbar.panels.request.RequestPanel",
        "debug_toolbar.panels.sql.SQLPanel",
        "debug_toolbar.panels.staticfiles.StaticFilesPanel",
        "debug_toolbar.panels.templates.TemplatesPanel",
        "debug_toolbar.panels.cache.CachePanel",
        "debug_toolbar.panels.signals.SignalsPanel",
    ]

# ─────────────────────────────────────────────────────────────────────────────
# 17. SENTRY (production uniquement)
# ─────────────────────────────────────────────────────────────────────────────
SENTRY_DSN = env("SENTRY_DSN")

if SENTRY_DSN:
    import sentry_sdk
    from sentry_sdk.integrations.django import DjangoIntegration
    from sentry_sdk.integrations.celery import CeleryIntegration
    from sentry_sdk.integrations.redis import RedisIntegration

    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[
            DjangoIntegration(transaction_style="url", middleware_spans=True),
            CeleryIntegration(monitor_beat_tasks=True),
            RedisIntegration(),
        ],
        traces_sample_rate=0.2,
        send_default_pii=False,
        environment="production" if not DEBUG else "development",
        release=env("APP_VERSION"),
    )

# ─────────────────────────────────────────────────────────────────────────────
# 18. DOCUMENTATION API
# ─────────────────────────────────────────────────────────────────────────────
SPECTACULAR_SETTINGS = {
    "TITLE":               "PharmaLink API",
    "DESCRIPTION":         "API centrale pour la plateforme de localisation et gestion de pharmacies.",
    "VERSION":             env("APP_VERSION"),
    "SERVE_INCLUDE_SCHEMA": False,
}