# apps/gardes/urls.py
from django.urls import path
from .views import (
    GardesActivesPublicView,
    GardesProchainesPublicView,
    HistoriqueGardesPublicView,
    MesGardesView,
    MaGardeDetailView,
    AdminGardesListView,
    AdminGardeDetailView,
)

urlpatterns = [

    # ── Public — app mobile ───────────────────────────────────────────────────
    path("",              GardesActivesPublicView.as_view(),    name="gardes-actives"),
    path("prochaines/",   GardesProchainesPublicView.as_view(), name="gardes-prochaines"),
    path("historique/",   HistoriqueGardesPublicView.as_view(), name="gardes-historique"),

    # ── Pharmacien ────────────────────────────────────────────────────────────
    path("mes-gardes/",          MesGardesView.as_view(),       name="mes-gardes"),
    path("mes-gardes/<int:pk>/", MaGardeDetailView.as_view(),   name="ma-garde-detail"),

    # ── Admin ─────────────────────────────────────────────────────────────────
    path("admin/",          AdminGardesListView.as_view(),  name="admin-gardes-list"),
    path("admin/<int:pk>/", AdminGardeDetailView.as_view(), name="admin-garde-detail"),
]