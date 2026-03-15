# apps/horaires/views.py
from datetime import date, timedelta
from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import HoraireSemaine, HoraireExceptionnel, est_ouverte_maintenant
from .serializers import (
    HoraireSemaineSerializer,
    HoraireSemaineBulkSerializer,
    HoraireExceptionnelSerializer,
    HorairesCompletSerializer,
)
from apps.users.permissions import IsPharmacien
from apps.pharmacies.models import Pharmacie


def get_pharmacie_ou_404(pharmacie_id, user=None):
    try:
        qs = Pharmacie.objects.filter(pk=pharmacie_id)
        if user:
            qs = qs.filter(pharmacien=user)
        return qs.get()
    except Pharmacie.DoesNotExist:
        return None


# ─────────────────────────────────────────────────────────────────────────────
# APP MOBILE — LECTURE PUBLIQUE
# ─────────────────────────────────────────────────────────────────────────────

class HorairesPublicView(APIView):
    """GET /api/v1/horaires/pharmacie/<pharmacie_id>/
    Horaires complets + statut ouverture en temps réel.
    Accessible sans authentification.
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request, pharmacie_id):
        try:
            pharmacie = Pharmacie.objects.get(pk=pharmacie_id, statut="active")
        except Pharmacie.DoesNotExist:
            return Response(
                {"error": "Pharmacie introuvable."},
                status=status.HTTP_404_NOT_FOUND,
            )

        semaine    = HoraireSemaine.objects.filter(pharmacie=pharmacie)
        exceptions = HoraireExceptionnel.objects.filter(
            pharmacie=pharmacie,
            date__gte=date.today(),
            date__lte=date.today() + timedelta(days=30),
        )

        serializer = HorairesCompletSerializer({
            "semaine":                list(semaine),
            "exceptions":             list(exceptions),
            "est_ouverte_maintenant": est_ouverte_maintenant(pharmacie),
        })
        return Response(serializer.data)


# ─────────────────────────────────────────────────────────────────────────────
# PHARMACIEN — GESTION DE SES HORAIRES
# ─────────────────────────────────────────────────────────────────────────────

class HoraireSemaineListView(generics.ListAPIView):
    """GET /api/v1/horaires/pharmacie/<pharmacie_id>/semaine/"""
    serializer_class   = HoraireSemaineSerializer
    permission_classes = [IsPharmacien]

    def get_queryset(self):
        return HoraireSemaine.objects.filter(
            pharmacie_id=self.kwargs["pharmacie_id"],
            pharmacie__pharmacien=self.request.user,
        )


class HoraireSemaineBulkView(APIView):
    """POST /api/v1/horaires/pharmacie/<pharmacie_id>/semaine/bulk/
    Mise à jour des 7 jours en une seule requête.
    """
    permission_classes = [IsPharmacien]

    def post(self, request, pharmacie_id):
        pharmacie = get_pharmacie_ou_404(pharmacie_id, user=request.user)
        if not pharmacie:
            return Response(
                {"error": "Pharmacie introuvable ou accès refusé."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = HoraireSemaineBulkSerializer(
            data=request.data,
            context={"pharmacie": pharmacie},
        )
        serializer.is_valid(raise_exception=True)
        resultats = serializer.save()

        return Response(
            {
                "message": (
                    f"{resultats['crees']} horaire(s) créé(s), "
                    f"{resultats['mis_a_jour']} mis à jour."
                ),
                "horaires": HoraireSemaineSerializer(
                    HoraireSemaine.objects.filter(pharmacie=pharmacie),
                    many=True,
                ).data,
            },
            status=status.HTTP_200_OK,
        )


class HoraireSemaineDetailView(generics.RetrieveUpdateAPIView):
    """GET/PATCH /api/v1/horaires/pharmacie/<pharmacie_id>/semaine/<id>/"""
    serializer_class   = HoraireSemaineSerializer
    permission_classes = [IsPharmacien]

    def get_queryset(self):
        return HoraireSemaine.objects.filter(
            pharmacie_id=self.kwargs["pharmacie_id"],
            pharmacie__pharmacien=self.request.user,
        )


class HoraireExceptionnelListView(generics.ListCreateAPIView):
    """GET/POST /api/v1/horaires/pharmacie/<pharmacie_id>/exceptions/"""
    serializer_class   = HoraireExceptionnelSerializer
    permission_classes = [IsPharmacien]

    def get_queryset(self):
        return HoraireExceptionnel.objects.filter(
            pharmacie_id=self.kwargs["pharmacie_id"],
            pharmacie__pharmacien=self.request.user,
        )

    def perform_create(self, serializer):
        pharmacie = get_pharmacie_ou_404(
            self.kwargs["pharmacie_id"], user=self.request.user
        )
        if not pharmacie:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Pharmacie introuvable ou accès refusé.")
        serializer.save(pharmacie=pharmacie)


class HoraireExceptionnelDetailView(generics.RetrieveUpdateDestroyAPIView):
    """GET/PATCH/DELETE /api/v1/horaires/pharmacie/<pharmacie_id>/exceptions/<id>/"""
    serializer_class   = HoraireExceptionnelSerializer
    permission_classes = [IsPharmacien]

    def get_queryset(self):
        return HoraireExceptionnel.objects.filter(
            pharmacie_id=self.kwargs["pharmacie_id"],
            pharmacie__pharmacien=self.request.user,
        )