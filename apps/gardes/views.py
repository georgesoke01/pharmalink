# apps/gardes/views.py
from django.utils import timezone
from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import PeriodeGarde
from .serializers import (
    PeriodeGardePublicSerializer,
    PeriodeGardeCreateSerializer,
    PeriodeGardeUpdateSerializer,
    PeriodeGardeAdminSerializer,
)
from apps.users.permissions import IsPharmacien, IsSuperAdmin
from apps.pharmacies.models import Pharmacie


# ─────────────────────────────────────────────────────────────────────────────
# APP MOBILE — LECTURE PUBLIQUE
# ─────────────────────────────────────────────────────────────────────────────

class GardesActivesPublicView(generics.ListAPIView):
    """GET /api/v1/gardes/
    Liste les gardes actives en ce moment.
    Filtrable par ville : ?ville=Cotonou
    Accessible sans authentification.
    """
    serializer_class   = PeriodeGardePublicSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        maintenant = timezone.now()
        qs = PeriodeGarde.objects.filter(
            statut=PeriodeGarde.Statut.EN_COURS,
            date_debut__lte=maintenant,
            date_fin__gte=maintenant,
            pharmacie__statut="active",
        ).select_related("pharmacie")

        ville = self.request.query_params.get("ville")
        if ville:
            qs = qs.filter(zone_ville__icontains=ville)
        return qs


class GardesProchainesPublicView(generics.ListAPIView):
    """GET /api/v1/gardes/prochaines/
    Gardes planifiées dans les 7 prochains jours.
    Filtrable par ville : ?ville=Porto-Novo
    """
    serializer_class   = PeriodeGardePublicSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        maintenant   = timezone.now()
        dans_7_jours = maintenant + timezone.timedelta(days=7)
        qs = PeriodeGarde.objects.filter(
            statut=PeriodeGarde.Statut.PLANIFIEE,
            date_debut__gte=maintenant,
            date_debut__lte=dans_7_jours,
            pharmacie__statut="active",
        ).select_related("pharmacie").order_by("date_debut")

        ville = self.request.query_params.get("ville")
        if ville:
            qs = qs.filter(zone_ville__icontains=ville)
        return qs


class HistoriqueGardesPublicView(generics.ListAPIView):
    """GET /api/v1/gardes/historique/
    Historique des gardes passées (30 derniers jours).
    Accessible sans authentification.
    """
    serializer_class   = PeriodeGardePublicSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        il_y_a_30j = timezone.now() - timezone.timedelta(days=30)
        return PeriodeGarde.objects.filter(
            statut=PeriodeGarde.Statut.TERMINEE,
            date_fin__gte=il_y_a_30j,
            pharmacie__statut="active",
        ).select_related("pharmacie").order_by("-date_fin")


# ─────────────────────────────────────────────────────────────────────────────
# PHARMACIEN — GESTION DE SES GARDES
# ─────────────────────────────────────────────────────────────────────────────

class MesGardesView(generics.ListCreateAPIView):
    """GET  /api/v1/gardes/mes-gardes/         → liste ses gardes
    POST /api/v1/gardes/mes-gardes/         → déclare une nouvelle garde

    Filtres :
        ?statut=planifiee | en_cours | terminee | annulee
        ?pharmacie_id=3
    """
    permission_classes = [IsPharmacien]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return PeriodeGardeCreateSerializer
        return PeriodeGardePublicSerializer

    def get_queryset(self):
        qs = PeriodeGarde.objects.filter(
            pharmacie__pharmacien=self.request.user,
        ).select_related("pharmacie").order_by("-date_debut")

        statut       = self.request.query_params.get("statut")
        pharmacie_id = self.request.query_params.get("pharmacie_id")

        if statut:
            qs = qs.filter(statut=statut)
        if pharmacie_id:
            qs = qs.filter(pharmacie_id=pharmacie_id)
        return qs

    def create(self, request, *args, **kwargs):
        pharmacie_id = request.data.get("pharmacie_id")

        # Récupère la pharmacie du pharmacien connecté
        try:
            pharmacie = Pharmacie.objects.get(
                pk=pharmacie_id,
                pharmacien=request.user,
                statut="active",
            )
        except Pharmacie.DoesNotExist:
            return Response(
                {"error": "Pharmacie introuvable, inactive ou non autorisée."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = PeriodeGardeCreateSerializer(
            data=request.data,
            context={"pharmacie": pharmacie, "request": request},
        )
        serializer.is_valid(raise_exception=True)
        garde = serializer.save()

        return Response(
            {
                "message": "Garde déclarée avec succès.",
                "garde": PeriodeGardePublicSerializer(garde).data,
            },
            status=status.HTTP_201_CREATED,
        )


class MaGardeDetailView(generics.RetrieveUpdateDestroyAPIView):
    """GET    /api/v1/gardes/mes-gardes/<id>/
    PATCH  /api/v1/gardes/mes-gardes/<id>/   → modifier (si PLANIFIEE)
    DELETE /api/v1/gardes/mes-gardes/<id>/   → annuler
    """
    permission_classes = [IsPharmacien]

    def get_serializer_class(self):
        if self.request.method in ["PUT", "PATCH"]:
            return PeriodeGardeUpdateSerializer
        return PeriodeGardePublicSerializer

    def get_queryset(self):
        return PeriodeGarde.objects.filter(
            pharmacie__pharmacien=self.request.user,
        ).select_related("pharmacie")

    def destroy(self, request, *args, **kwargs):
        """Annule la garde au lieu de la supprimer."""
        garde = self.get_object()
        if garde.statut == PeriodeGarde.Statut.TERMINEE:
            return Response(
                {"error": "Une garde terminée ne peut pas être annulée."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        garde.annuler()
        return Response(
            {"message": "Garde annulée avec succès."},
            status=status.HTTP_200_OK,
        )


# ─────────────────────────────────────────────────────────────────────────────
# ADMIN — SUPERVISION COMPLÈTE
# ─────────────────────────────────────────────────────────────────────────────

class AdminGardesListView(generics.ListAPIView):
    """GET /api/v1/gardes/admin/
    Liste toutes les gardes — tous statuts.
    Filtres : ?statut=en_cours  ?ville=Cotonou  ?pharmacie_id=3
    """
    serializer_class   = PeriodeGardeAdminSerializer
    permission_classes = [IsSuperAdmin]

    def get_queryset(self):
        qs = PeriodeGarde.objects.all().select_related("pharmacie").order_by("-date_debut")

        statut       = self.request.query_params.get("statut")
        ville        = self.request.query_params.get("ville")
        pharmacie_id = self.request.query_params.get("pharmacie_id")

        if statut:
            qs = qs.filter(statut=statut)
        if ville:
            qs = qs.filter(zone_ville__icontains=ville)
        if pharmacie_id:
            qs = qs.filter(pharmacie_id=pharmacie_id)
        return qs


class AdminGardeDetailView(generics.RetrieveUpdateDestroyAPIView):
    """GET/PATCH/DELETE /api/v1/gardes/admin/<id>/
    Super admin uniquement.
    """
    serializer_class   = PeriodeGardeAdminSerializer
    permission_classes = [IsSuperAdmin]
    queryset           = PeriodeGarde.objects.all().select_related("pharmacie")

    def destroy(self, request, *args, **kwargs):
        garde = self.get_object()
        garde.annuler()
        return Response(
            {"message": "Garde annulée par l'administrateur."},
            status=status.HTTP_200_OK,
        )