# config/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenBlacklistView,
)
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)


# ── Health check ─────────────────────────────────────────────────────────────
def health_check(request):
    """Endpoint de monitoring — vérifie que l'API est opérationnelle.

    Utilisé par :
      - Contabo / Docker pour les checks de santé du conteneur
      - Nginx upstream health checks
      - Monitoring externe (UptimeRobot, etc.)

    Returns:
        200 { status, version, environment }  → API opérationnelle
        500                                   → Erreur critique (géré par Django)
    """
    from django.db import connection
    from django.core.cache import cache

    # Vérification DB
    db_ok = True
    try:
        connection.ensure_connection()
    except Exception:
        db_ok = False

    # Vérification Redis (cache)
    cache_ok = True
    try:
        cache.set("health_check_ping", "pong", timeout=5)
        cache_ok = cache.get("health_check_ping") == "pong"
    except Exception:
        cache_ok = False

    status_code = 200 if (db_ok and cache_ok) else 503
    return JsonResponse(
        {
            "status":      "ok" if status_code == 200 else "degraded",
            "version":     settings.SPECTACULAR_SETTINGS.get("VERSION", "1.0.0"),
            "environment": "production" if not settings.DEBUG else "development",
            "checks": {
                "database": "ok" if db_ok    else "error",
                "cache":    "ok" if cache_ok else "error",
            },
        },
        status=status_code,
    )


# ── URL patterns ──────────────────────────────────────────────────────────────
urlpatterns = [
    # ── Admin Django ─────────────────────────────────────────────────────────
    path("admin/", admin.site.urls),

    # ── Monitoring ───────────────────────────────────────────────────────────
    path("api/health/", health_check, name="health-check"),

    # ── Authentification JWT ─────────────────────────────────────────────────
    path("api/v1/auth/token/",         TokenObtainPairView.as_view(),  name="token_obtain_pair"),
    path("api/v1/auth/token/refresh/", TokenRefreshView.as_view(),     name="token_refresh"),
    path("api/v1/auth/token/logout/",  TokenBlacklistView.as_view(),   name="token_blacklist"),

    # ── Apps métier ──────────────────────────────────────────────────────────
    path("api/v1/users/",      include("apps.users.urls")),
    path("api/v1/pharmacies/", include("apps.pharmacies.urls")),
    path("api/v1/produits/",   include("apps.produits.urls")),
    path("api/v1/horaires/",   include("apps.horaires.urls")),
    path("api/v1/gardes/",     include("apps.gardes.urls")),
    path("api/v1/lgo/",        include("apps.connecteurs_lgo.urls")),

    # ── Documentation OpenAPI ────────────────────────────────────────────────
    path("api/schema/",  SpectacularAPIView.as_view(),                          name="schema"),
    path("api/docs/",    SpectacularSwaggerView.as_view(url_name="schema"),     name="swagger-ui"),
    path("api/redoc/",   SpectacularRedocView.as_view(url_name="schema"),       name="redoc"),
]

# ── Debug Toolbar (développement uniquement) ──────────────────────────────────
if settings.DEBUG:
    import debug_toolbar
    urlpatterns = [
        path("__debug__/", include(debug_toolbar.urls)),
    ] + urlpatterns

# ── Serving fichiers media et static (développement uniquement) ───────────────
# En production, Nginx sert directement ces fichiers — Django ne doit pas s'en charger
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,  document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)