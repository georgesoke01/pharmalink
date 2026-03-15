# apps/connecteurs_lgo/urls.py
from django.urls import path
from .views import (
    DetectionLGOView,
    TestConnexionView,
    SyncManuelleView,
    StatutConnexionView,
    LogsSyncView,
    AdminConnexionsListView,
    AdminStatsView,
)

urlpatterns = [

    # ── Auto-détection Tauri ──────────────────────────────────────────────────
    path("detection/",                      DetectionLGOView.as_view(),         name="lgo-detection"),

    # ── Pharmacien ────────────────────────────────────────────────────────────
    path("test/<int:pharmacie_id>/",        TestConnexionView.as_view(),        name="lgo-test"),
    path("sync/<int:pharmacie_id>/",        SyncManuelleView.as_view(),         name="lgo-sync-manuelle"),
    path("statut/<int:pharmacie_id>/",      StatutConnexionView.as_view(),      name="lgo-statut"),
    path("logs/<int:pharmacie_id>/",        LogsSyncView.as_view(),             name="lgo-logs"),

    # ── Admin ─────────────────────────────────────────────────────────────────
    path("admin/connexions/",               AdminConnexionsListView.as_view(),  name="lgo-admin-list"),
    path("admin/stats/",                    AdminStatsView.as_view(),           name="lgo-admin-stats"),
]