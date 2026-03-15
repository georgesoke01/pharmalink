# apps/users/urls.py
from django.urls import path
from .views import (
    InscriptionPublicView,
    InscriptionPharmacienView,
    MonProfilView,
    UpdatePasswordView,
    AdminUserListView,
    AdminUserDetailView,
    AdminApprobationView,
    AdminPharmacienEnAttenteView,
)

urlpatterns = [

    # ── Inscription ───────────────────────────────────────────────────────────
    path("inscription/public/",      InscriptionPublicView.as_view(),      name="inscription-public"),
    path("inscription/pharmacien/",  InscriptionPharmacienView.as_view(),  name="inscription-pharmacien"),

    # ── Profil utilisateur connecté ───────────────────────────────────────────
    path("moi/",                     MonProfilView.as_view(),              name="mon-profil"),
    path("moi/password/",            UpdatePasswordView.as_view(),         name="update-password"),

    # ── Admin ─────────────────────────────────────────────────────────────────
    path("admin/",                   AdminUserListView.as_view(),          name="admin-user-list"),
    path("admin/en-attente/",        AdminPharmacienEnAttenteView.as_view(), name="admin-en-attente"),
    path("admin/<int:pk>/",          AdminUserDetailView.as_view(),        name="admin-user-detail"),
    path("admin/<int:pk>/approbation/", AdminApprobationView.as_view(),    name="admin-approbation"),
]