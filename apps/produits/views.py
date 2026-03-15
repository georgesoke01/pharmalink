# apps/produits/views.py
from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Produit, Stock, Prix
from .serializers import (
    ProduitPublicSerializer,
    ProduitDetailSerializer,
    ProduitCreateSerializer,
    ProduitUpdateSerializer,
    ProduitAvecPrixStockSerializer,
    StockSerializer,
    StockUpdateSerializer,
    StockBulkUpdateSerializer,
    PrixSerializer,
    PrixUpdateSerializer,
    PrixBulkUpdateSerializer,
)
from .filters import ProduitFilter, StockFilter
from apps.users.permissions import IsPharmacien, IsSuperAdmin, IsOwnerOrSuperAdmin
from apps.pharmacies.models import Pharmacie


# ─────────────────────────────────────────────────────────────────────────────
# PRODUITS — ACCÈS PUBLIC (app mobile)
# ─────────────────────────────────────────────────────────────────────────────

class ProduitListPublicView(generics.ListAPIView):
    """GET /api/v1/produits/
    Catalogue global des produits.
    Accessible sans authentification.

    Filtres :
        ?search=paracetamol
        ?categorie=medicament
        ?sur_ordonnance=true
        ?forme=comprimes
        ?disponible=true
        ?pharmacie_id=3     → produits dispo dans cette pharmacie
        ?page_size=20
    """
    serializer_class   = ProduitPublicSerializer
    permission_classes = [permissions.AllowAny]
    filterset_class    = ProduitFilter
    queryset           = Produit.objects.all()


class ProduitDetailPublicView(generics.RetrieveAPIView):
    """GET /api/v1/produits/<id>/
    Fiche détaillée d'un produit.
    Accessible sans authentification.
    """
    serializer_class   = ProduitDetailSerializer
    permission_classes = [permissions.AllowAny]
    queryset           = Produit.objects.all()


class ProduitParPharmacieView(generics.ListAPIView):
    """GET /api/v1/produits/pharmacie/<pharmacie_id>/
    Produits disponibles dans une pharmacie donnée, avec prix et stock.
    Utilisé par l'app mobile sur la fiche d'une pharmacie.
    """
    serializer_class   = ProduitAvecPrixStockSerializer
    permission_classes = [permissions.AllowAny]
    filterset_class    = ProduitFilter

    def get_queryset(self):
        pharmacie_id = self.kwargs["pharmacie_id"]
        return (
            Produit.objects
            .filter(
                stocks__pharmacie_id=pharmacie_id,
                stocks__disponible=True,
            )
            .distinct()
            .order_by("nom")
        )

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        # Injecte pharmacie_id dans le contexte pour les serializers de prix/stock
        ctx["pharmacie_id"] = self.kwargs.get("pharmacie_id")
        return ctx


# ─────────────────────────────────────────────────────────────────────────────
# PRODUITS — GESTION (pharmacien + admin)
# ─────────────────────────────────────────────────────────────────────────────

class ProduitCreateView(generics.CreateAPIView):
    """POST /api/v1/produits/creer/
    Crée un nouveau produit dans le catalogue global.
    Réservé aux pharmaciens approuvés et aux super admins.
    """
    serializer_class   = ProduitCreateSerializer
    permission_classes = [IsPharmacien | IsSuperAdmin]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        produit = serializer.save()
        return Response(
            {
                "message": "Produit créé avec succès.",
                "produit": ProduitDetailSerializer(produit).data,
            },
            status=status.HTTP_201_CREATED,
        )


class ProduitUpdateView(generics.UpdateAPIView):
    """PATCH /api/v1/produits/<id>/modifier/
    Met à jour un produit. Super admin uniquement.
    """
    serializer_class   = ProduitUpdateSerializer
    permission_classes = [IsSuperAdmin]
    queryset           = Produit.objects.all()


# ─────────────────────────────────────────────────────────────────────────────
# STOCKS — GESTION (pharmacien)
# ─────────────────────────────────────────────────────────────────────────────

class StockListView(generics.ListAPIView):
    """GET /api/v1/produits/stocks/<pharmacie_id>/
    Liste les stocks d'une pharmacie.

    Filtres :
        ?disponible=true
        ?en_alerte=true    → stocks sous le seuil d'alerte
        ?search=doliprane
    """
    serializer_class   = StockSerializer
    permission_classes = [IsPharmacien]
    filterset_class    = StockFilter

    def get_queryset(self):
        pharmacie_id = self.kwargs["pharmacie_id"]
        # Vérifie que la pharmacie appartient au pharmacien connecté
        return (
            Stock.objects
            .filter(
                pharmacie_id=pharmacie_id,
                pharmacie__pharmacien=self.request.user,
            )
            .select_related("produit", "pharmacie")
            .order_by("produit__nom")
        )


class StockUpdateView(generics.UpdateAPIView):
    """PATCH /api/v1/produits/stocks/<pharmacie_id>/<produit_id>/
    Met à jour le stock d'un produit dans une pharmacie.
    Pharmacien propriétaire uniquement.
    """
    serializer_class   = StockUpdateSerializer
    permission_classes = [IsPharmacien]

    def get_object(self):
        pharmacie_id = self.kwargs["pharmacie_id"]
        produit_id   = self.kwargs["produit_id"]
        stock, _     = Stock.objects.get_or_create(
            pharmacie_id=pharmacie_id,
            produit_id=produit_id,
        )
        return stock


class StockBulkUpdateView(APIView):
    """POST /api/v1/produits/stocks/<pharmacie_id>/bulk/
    Mise à jour en masse des stocks — utilisé lors de l'import LGO.
    Pharmacien propriétaire uniquement.
    """
    permission_classes = [IsPharmacien]

    def post(self, request, pharmacie_id):
        try:
            pharmacie = Pharmacie.objects.get(
                pk=pharmacie_id,
                pharmacien=request.user,
            )
        except Pharmacie.DoesNotExist:
            return Response(
                {"error": "Pharmacie introuvable ou accès refusé."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = StockBulkUpdateSerializer(
            data=request.data,
            context={"pharmacie": pharmacie},
        )
        serializer.is_valid(raise_exception=True)
        results = serializer.save()

        return Response(
            {
                "message": f"{results['mis_a_jour']} stock(s) mis à jour.",
                "erreurs": results["erreurs"],
            },
            status=status.HTTP_200_OK,
        )


# ─────────────────────────────────────────────────────────────────────────────
# PRIX — GESTION (pharmacien)
# ─────────────────────────────────────────────────────────────────────────────

class PrixListView(generics.ListAPIView):
    """GET /api/v1/produits/prix/<pharmacie_id>/
    Liste les prix d'une pharmacie.
    """
    serializer_class   = PrixSerializer
    permission_classes = [IsPharmacien]

    def get_queryset(self):
        pharmacie_id = self.kwargs["pharmacie_id"]
        return (
            Prix.objects
            .filter(
                pharmacie_id=pharmacie_id,
                pharmacie__pharmacien=self.request.user,
            )
            .select_related("produit")
            .order_by("produit__nom")
        )


class PrixUpdateView(generics.UpdateAPIView):
    """PATCH /api/v1/produits/prix/<pharmacie_id>/<produit_id>/
    Met à jour le prix d'un produit dans une pharmacie.
    """
    serializer_class   = PrixUpdateSerializer
    permission_classes = [IsPharmacien]

    def get_object(self):
        pharmacie_id = self.kwargs["pharmacie_id"]
        produit_id   = self.kwargs["produit_id"]
        prix, _      = Prix.objects.get_or_create(
            pharmacie_id=pharmacie_id,
            produit_id=produit_id,
            defaults={"prix_fcfa": 0},
        )
        return prix


class PrixBulkUpdateView(APIView):
    """POST /api/v1/produits/prix/<pharmacie_id>/bulk/
    Mise à jour en masse des prix — import LGO.
    """
    permission_classes = [IsPharmacien]

    def post(self, request, pharmacie_id):
        try:
            pharmacie = Pharmacie.objects.get(
                pk=pharmacie_id,
                pharmacien=request.user,
            )
        except Pharmacie.DoesNotExist:
            return Response(
                {"error": "Pharmacie introuvable ou accès refusé."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = PrixBulkUpdateSerializer(
            data=request.data,
            context={"pharmacie": pharmacie},
        )
        serializer.is_valid(raise_exception=True)
        results = serializer.save()

        return Response(
            {
                "message": f"{results['mis_a_jour']} prix mis à jour.",
                "erreurs": results["erreurs"],
            },
            status=status.HTTP_200_OK,
        )


# ─────────────────────────────────────────────────────────────────────────────
# STOCKS EN ALERTE — DASHBOARD PHARMACIEN
# ─────────────────────────────────────────────────────────────────────────────

class StocksEnAlerteView(generics.ListAPIView):
    """GET /api/v1/produits/stocks/<pharmacie_id>/alertes/
    Stocks dont la quantité est sous le seuil d'alerte.
    Utilisé dans le dashboard du pharmacien.
    """
    serializer_class   = StockSerializer
    permission_classes = [IsPharmacien]

    def get_queryset(self):
        from django.db.models import F
        pharmacie_id = self.kwargs["pharmacie_id"]
        return (
            Stock.objects
            .filter(
                pharmacie_id=pharmacie_id,
                pharmacie__pharmacien=self.request.user,
                seuil_alerte__gt=0,
                quantite__lte=F("seuil_alerte"),
            )
            .select_related("produit")
            .order_by("quantite")
        )