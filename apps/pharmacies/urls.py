# apps/pharmacies/urls.py
from django.urls import path
from .views import (
    PharmacieListPublicView,
    PharmacieDetailPublicView,
    PharmaciesDeGardeView,
    MesPharmaciesView,
    MaPharmaciDetailView,
    AdminPharmacieListView,
    AdminPharmacieDetailView,
    AdminStatutPharmacieView,
    AdminPharmaciesEnAttenteView,
)

urlpatterns = [

    # ── Public — app mobile ───────────────────────────────────────────────────
    path("",                   PharmacieListPublicView.as_view(),       name="pharmacie-list"),
    path("<int:pk>/",          PharmacieDetailPublicView.as_view(),     name="pharmacie-detail"),
    path("de-garde/",          PharmaciesDeGardeView.as_view(),         name="pharmacies-de-garde"),

    # ── Pharmacien — ses pharmacies ───────────────────────────────────────────
    path("mes-pharmacies/",            MesPharmaciesView.as_view(),     name="mes-pharmacies"),
    path("mes-pharmacies/<int:pk>/",   MaPharmaciDetailView.as_view(),  name="ma-pharmacie-detail"),

    # ── Admin ─────────────────────────────────────────────────────────────────
    path("admin/",                     AdminPharmacieListView.as_view(),       name="admin-pharmacie-list"),
    path("admin/en-attente/",          AdminPharmaciesEnAttenteView.as_view(), name="admin-pharmacies-en-attente"),
    path("admin/<int:pk>/",            AdminPharmacieDetailView.as_view(),     name="admin-pharmacie-detail"),
    path("admin/<int:pk>/statut/",     AdminStatutPharmacieView.as_view(),     name="admin-pharmacie-statut"),
]