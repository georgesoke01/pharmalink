# apps/pharmacies/views.py
from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Pharmacie
from .serializers import (
    PharmaciePublicSerializer,
    PharmacieDetailSerializer,
    PharmacieCreateSerializer,
    PharmacieUpdateSerializer,
    PharmacieAdminSerializer,
    AdminStatutSerializer,
)
from .filters import PharmacieFilter
from apps.users.permissions import (
    IsPharmacien,
    IsSuperAdmin,
    IsOwnerOrSuperAdmin,
    ReadOnly,
)


# ─────────────────────────────────────────────────────────────────────────────
# APP MOBILE — ACCÈS PUBLIC
# ─────────────────────────────────────────────────────────────────────────────

class PharmacieListPublicView(generics.ListAPIView):
    """GET /api/v1/pharmacies/
    Liste publique des pharmacies actives.
    Accessible sans authentification (app mobile).

    Filtres disponibles :
        ?ville=Cotonou
        ?est_ouverte=true
        ?est_de_garde=true
        ?service=livraison
        ?lat=6.37&lng=2.39&rayon=5    → dans un rayon de 5km
        ?search=pharmacie+centrale
        ?page_size=10
    """
    serializer_class   = PharmaciePublicSerializer
    permission_classes = [permissions.AllowAny]
    filterset_class    = PharmacieFilter

    def get_queryset(self):
        return (
            Pharmacie.objects
            .filter(statut=Pharmacie.Statut.ACTIVE)
            .select_related("pharmacien")
            .order_by("nom")
        )


class PharmacieDetailPublicView(generics.RetrieveAPIView):
    """GET /api/v1/pharmacies/<id>/
    Fiche détaillée d'une pharmacie — app mobile.
    Accessible sans authentification.
    """
    serializer_class   = PharmacieDetailSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        return (
            Pharmacie.objects
            .filter(statut=Pharmacie.Statut.ACTIVE)
            .select_related("pharmacien")
            .prefetch_related("horaires_semaine", "periodes_garde")
        )


class PharmaciesDeGardeView(generics.ListAPIView):
    """GET /api/v1/pharmacies/de-garde/
    Liste des pharmacies de garde en ce moment.
    Filtrable par ville : ?ville=Cotonou
    """
    serializer_class   = PharmaciePublicSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        qs = (
            Pharmacie.objects
            .filter(statut=Pharmacie.Statut.ACTIVE, est_de_garde=True)
            .select_related("pharmacien")
        )
        ville = self.request.query_params.get("ville")
        if ville:
            qs = qs.filter(ville__icontains=ville)
        return qs


# ─────────────────────────────────────────────────────────────────────────────
# PHARMACIEN — GESTION DE SES PHARMACIES
# ─────────────────────────────────────────────────────────────────────────────

class MesPharmaciesView(generics.ListCreateAPIView):
    """GET  /api/v1/pharmacies/mes-pharmacies/  → liste ses pharmacies
    POST /api/v1/pharmacies/mes-pharmacies/  → crée une pharmacie
    Réservé au pharmacien connecté et approuvé.
    """
    permission_classes = [IsPharmacien]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return PharmacieCreateSerializer
        return PharmacieDetailSerializer

    def get_queryset(self):
        return (
            Pharmacie.objects
            .filter(pharmacien=self.request.user)
            .order_by("-created_at")
        )

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        pharmacie = serializer.save()
        return Response(
            {
                "message": (
                    "Pharmacie enregistrée avec succès. "
                    "Elle sera visible après validation par un administrateur."
                ),
                "pharmacie": PharmacieDetailSerializer(pharmacie).data,
            },
            status=status.HTTP_201_CREATED,
        )


class MaPharmaciDetailView(generics.RetrieveUpdateAPIView):
    """GET   /api/v1/pharmacies/mes-pharmacies/<id>/  → détail
    PATCH /api/v1/pharmacies/mes-pharmacies/<id>/  → mise à jour
    Un pharmacien ne peut accéder qu'à ses propres pharmacies.
    """
    permission_classes = [IsPharmacien, IsOwnerOrSuperAdmin]

    def get_serializer_class(self):
        if self.request.method in ["PUT", "PATCH"]:
            return PharmacieUpdateSerializer
        return PharmacieDetailSerializer

    def get_queryset(self):
        return Pharmacie.objects.filter(pharmacien=self.request.user)


# ─────────────────────────────────────────────────────────────────────────────
# ADMIN — SUPERVISION COMPLÈTE
# ─────────────────────────────────────────────────────────────────────────────

class AdminPharmacieListView(generics.ListAPIView):
    """GET /api/v1/pharmacies/admin/
    Liste toutes les pharmacies (tous statuts).
    Filtres : ?statut=en_attente  ?ville=Porto-Novo
    Super admin uniquement.
    """
    serializer_class   = PharmacieAdminSerializer
    permission_classes = [IsSuperAdmin]
    filterset_class    = PharmacieFilter

    def get_queryset(self):
        return (
            Pharmacie.objects
            .all()
            .select_related("pharmacien")
            .order_by("-created_at")
        )


class AdminPharmacieDetailView(generics.RetrieveUpdateDestroyAPIView):
    """GET    /api/v1/pharmacies/admin/<id>/
    PATCH  /api/v1/pharmacies/admin/<id>/
    DELETE /api/v1/pharmacies/admin/<id>/
    Super admin uniquement.
    """
    serializer_class   = PharmacieAdminSerializer
    permission_classes = [IsSuperAdmin]
    queryset           = Pharmacie.objects.all().select_related("pharmacien")


class AdminStatutPharmacieView(APIView):
    """POST /api/v1/pharmacies/admin/<id>/statut/
    Activer ou suspendre une pharmacie.
    Body : { "action": "activer" | "suspendre", "raison": "..." }
    Super admin uniquement.
    """
    permission_classes = [IsSuperAdmin]

    def post(self, request, pk):
        try:
            pharmacie = Pharmacie.objects.get(pk=pk)
        except Pharmacie.DoesNotExist:
            return Response(
                {"error": "Pharmacie introuvable."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = AdminStatutSerializer(
            data=request.data,
            context={"pharmacie": pharmacie, "request": request},
        )
        serializer.is_valid(raise_exception=True)
        pharmacie = serializer.save()

        action  = serializer.validated_data["action"]
        message = (
            f"Pharmacie '{pharmacie.nom}' activée avec succès."
            if action == "activer"
            else f"Pharmacie '{pharmacie.nom}' suspendue."
        )
        return Response(
            {"message": message, "pharmacie": PharmacieAdminSerializer(pharmacie).data},
            status=status.HTTP_200_OK,
        )


class AdminPharmaciesEnAttenteView(generics.ListAPIView):
    """GET /api/v1/pharmacies/admin/en-attente/
    Raccourci : liste les pharmacies en attente d'approbation.
    """
    serializer_class   = PharmacieAdminSerializer
    permission_classes = [IsSuperAdmin]

    def get_queryset(self):
        return (
            Pharmacie.objects
            .filter(statut=Pharmacie.Statut.EN_ATTENTE)
            .select_related("pharmacien")
            .order_by("created_at")
        )