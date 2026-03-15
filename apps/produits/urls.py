# apps/produits/urls.py
from django.urls import path
from .views import (
    ProduitListPublicView,
    ProduitDetailPublicView,
    ProduitParPharmacieView,
    ProduitCreateView,
    ProduitUpdateView,
    StockListView,
    StockUpdateView,
    StockBulkUpdateView,
    StocksEnAlerteView,
    PrixListView,
    PrixUpdateView,
    PrixBulkUpdateView,
)

urlpatterns = [

    # ── Public — app mobile ───────────────────────────────────────────────────
    path("",                                  ProduitListPublicView.as_view(),    name="produit-list"),
    path("<int:pk>/",                         ProduitDetailPublicView.as_view(),  name="produit-detail"),
    path("pharmacie/<int:pharmacie_id>/",     ProduitParPharmacieView.as_view(),  name="produits-par-pharmacie"),

    # ── Gestion produits (pharmacien / admin) ─────────────────────────────────
    path("creer/",                            ProduitCreateView.as_view(),        name="produit-creer"),
    path("<int:pk>/modifier/",                ProduitUpdateView.as_view(),        name="produit-modifier"),

    # ── Stocks ────────────────────────────────────────────────────────────────
    path("stocks/<int:pharmacie_id>/",                           StockListView.as_view(),        name="stock-list"),
    path("stocks/<int:pharmacie_id>/bulk/",                      StockBulkUpdateView.as_view(),  name="stock-bulk"),
    path("stocks/<int:pharmacie_id>/alertes/",                   StocksEnAlerteView.as_view(),   name="stock-alertes"),
    path("stocks/<int:pharmacie_id>/<int:produit_id>/",          StockUpdateView.as_view(),      name="stock-update"),

    # ── Prix ──────────────────────────────────────────────────────────────────
    path("prix/<int:pharmacie_id>/",                             PrixListView.as_view(),         name="prix-list"),
    path("prix/<int:pharmacie_id>/bulk/",                        PrixBulkUpdateView.as_view(),   name="prix-bulk"),
    path("prix/<int:pharmacie_id>/<int:produit_id>/",            PrixUpdateView.as_view(),       name="prix-update"),
]