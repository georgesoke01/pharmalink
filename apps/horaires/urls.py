# apps/horaires/urls.py
from django.urls import path
from .views import (
    HorairesPublicView,
    HoraireSemaineListView,
    HoraireSemaineBulkView,
    HoraireSemaineDetailView,
    HoraireExceptionnelListView,
    HoraireExceptionnelDetailView,
)

urlpatterns = [

    # ── Public — app mobile ───────────────────────────────────────────────────
    path("pharmacie/<int:pharmacie_id>/",                  HorairesPublicView.as_view(),             name="horaires-public"),

    # ── Horaires semaine ──────────────────────────────────────────────────────
    path("pharmacie/<int:pharmacie_id>/semaine/",          HoraireSemaineListView.as_view(),          name="horaire-semaine-list"),
    path("pharmacie/<int:pharmacie_id>/semaine/bulk/",     HoraireSemaineBulkView.as_view(),          name="horaire-semaine-bulk"),
    path("pharmacie/<int:pharmacie_id>/semaine/<int:pk>/", HoraireSemaineDetailView.as_view(),        name="horaire-semaine-detail"),

    # ── Horaires exceptionnels ────────────────────────────────────────────────
    path("pharmacie/<int:pharmacie_id>/exceptions/",          HoraireExceptionnelListView.as_view(),   name="horaire-excep-list"),
    path("pharmacie/<int:pharmacie_id>/exceptions/<int:pk>/", HoraireExceptionnelDetailView.as_view(), name="horaire-excep-detail"),
]