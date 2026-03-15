# apps/connecteurs_lgo/views.py
from django.utils import timezone
from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import ConnexionLGO, LogSync
from .serializers import (
    DetectionLGOSerializer,
    ConnexionLGOSerializer,
    LogSyncSerializer,
    StatsSyncSerializer,
)
from .tasks import sync_pharmacie_lgo
from apps.users.permissions import IsPharmacien, IsSuperAdmin
from apps.pharmacies.models import Pharmacie


CONNECTEURS = {}

def get_connecteur(connexion: ConnexionLGO):
    """Instancie le bon connecteur selon le type de LGO."""
    from .pharmagest import ConnecteurPharmagest
    from .winpharma  import ConnecteurWinpharma

    registry = {
        "pharmagest": ConnecteurPharmagest,
        "winpharma":  ConnecteurWinpharma,
    }
    cls = registry.get(connexion.type_lgo)
    if not cls:
        return None
    return cls(connexion.config)


# ─────────────────────────────────────────────────────────────────────────────
# AUTO-DÉTECTION — reçoit le résultat du scan Tauri
# ─────────────────────────────────────────────────────────────────────────────

class DetectionLGOView(APIView):
    """POST /api/v1/lgo/detection/

    Reçoit le résultat de l'auto-détection du LGO par l'app Desktop Tauri.
    Crée ou met à jour la ConnexionLGO, teste la connexion,
    puis déclenche la première synchronisation.

    Body :
    {
        "pharmacie_id": 3,
        "type_lgo": "pharmagest",
        "version_lgo": "8.2.1",
        "poste_nom": "PC-PHARMACIE-01",
        "config": {
            "db_path": "C:\\\\Pharmagest\\\\Data\\\\pharma.db",
            "db_type": "sqlite"
        }
    }
    """
    permission_classes = [IsPharmacien]

    def post(self, request):
        serializer = DetectionLGOSerializer(
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        connexion, created = serializer.save()

        # ── Test de connexion immédiat ─────────────────────────────────────────
        connecteur = get_connecteur(connexion)
        if not connecteur:
            return Response(
                {"error": f"Type LGO '{connexion.type_lgo}' non supporté pour l'instant."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        connexion_ok = connecteur.tester_connexion()

        if not connexion_ok:
            connexion.marquer_erreur("Test de connexion échoué après détection.")
            return Response(
                {
                    "statut":  "erreur",
                    "message": (
                        "LGO détecté mais connexion impossible. "
                        "Vérifiez que le LGO est ouvert et que les permissions sont correctes."
                    ),
                    "connexion": ConnexionLGOSerializer(connexion).data,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ── Connexion OK → activation + première sync ─────────────────────────
        connexion.statut = ConnexionLGO.Statut.ACTIVE
        connexion.save(update_fields=["statut"])

        # Déclenche la première sync en arrière-plan (Celery)
        sync_pharmacie_lgo.apply_async(
            args=[connexion.pharmacie_id, "installation"],
            queue="high",
        )

        return Response(
            {
                "statut":  "ok",
                "message": (
                    f"{'Nouvelle connexion' if created else 'Connexion mise à jour'} — "
                    f"{connexion.get_type_lgo_display()} détecté avec succès. "
                    "Première synchronisation lancée en arrière-plan."
                ),
                "connexion": ConnexionLGOSerializer(connexion).data,
            },
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )


# ─────────────────────────────────────────────────────────────────────────────
# TEST DE CONNEXION
# ─────────────────────────────────────────────────────────────────────────────

class TestConnexionView(APIView):
    """POST /api/v1/lgo/test/<pharmacie_id>/

    Teste la connexion au LGO depuis le serveur Django.
    Utilisé par l'app Desktop pour vérifier que tout fonctionne.
    """
    permission_classes = [IsPharmacien]

    def post(self, request, pharmacie_id):
        try:
            connexion = ConnexionLGO.objects.get(
                pharmacie_id=pharmacie_id,
                pharmacie__pharmacien=request.user,
            )
        except ConnexionLGO.DoesNotExist:
            return Response(
                {"error": "Aucune connexion LGO configurée pour cette pharmacie."},
                status=status.HTTP_404_NOT_FOUND,
            )

        connecteur = get_connecteur(connexion)
        if not connecteur:
            return Response(
                {"error": f"Type LGO '{connexion.type_lgo}' non supporté."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        ok = connecteur.tester_connexion()

        if ok:
            connexion.statut = ConnexionLGO.Statut.ACTIVE
            connexion.save(update_fields=["statut"])
        else:
            connexion.marquer_erreur("Test de connexion manuel échoué.")

        return Response(
            {
                "connexion_ok": ok,
                "message":  "Connexion réussie." if ok else "Connexion échouée.",
                "connexion": ConnexionLGOSerializer(connexion).data,
            },
            status=status.HTTP_200_OK,
        )


# ─────────────────────────────────────────────────────────────────────────────
# SYNC MANUELLE
# ─────────────────────────────────────────────────────────────────────────────

class SyncManuelleView(APIView):
    """POST /api/v1/lgo/sync/<pharmacie_id>/

    Déclenche une synchronisation immédiate depuis le dashboard
    de l'app Desktop (bouton "Synchroniser maintenant").
    """
    permission_classes = [IsPharmacien]

    def post(self, request, pharmacie_id):
        try:
            connexion = ConnexionLGO.objects.get(
                pharmacie_id=pharmacie_id,
                pharmacie__pharmacien=request.user,
                statut=ConnexionLGO.Statut.ACTIVE,
            )
        except ConnexionLGO.DoesNotExist:
            return Response(
                {"error": "Aucune connexion LGO active pour cette pharmacie."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Lance la sync en arrière-plan via Celery (queue high = prioritaire)
        task = sync_pharmacie_lgo.apply_async(
            args=[pharmacie_id, "manuel"],
            queue="high",
        )

        return Response(
            {
                "message":  "Synchronisation lancée. Les données seront mises à jour dans quelques instants.",
                "task_id":  task.id,
                "pharmacie_id": pharmacie_id,
            },
            status=status.HTTP_202_ACCEPTED,
        )


# ─────────────────────────────────────────────────────────────────────────────
# STATUT & LOGS — pharmacien
# ─────────────────────────────────────────────────────────────────────────────

class StatutConnexionView(generics.RetrieveAPIView):
    """GET /api/v1/lgo/statut/<pharmacie_id>/

    Statut de la connexion LGO d'une pharmacie.
    Utilisé par l'app Desktop pour afficher le tableau de bord.
    """
    serializer_class   = ConnexionLGOSerializer
    permission_classes = [IsPharmacien]

    def get_object(self):
        try:
            return ConnexionLGO.objects.get(
                pharmacie_id=self.kwargs["pharmacie_id"],
                pharmacie__pharmacien=self.request.user,
            )
        except ConnexionLGO.DoesNotExist:
            from rest_framework.exceptions import NotFound
            raise NotFound("Aucune connexion LGO configurée pour cette pharmacie.")


class LogsSyncView(generics.ListAPIView):
    """GET /api/v1/lgo/logs/<pharmacie_id>/

    Historique des synchronisations d'une pharmacie.
    ?page_size=10 pour paginer.
    """
    serializer_class   = LogSyncSerializer
    permission_classes = [IsPharmacien]

    def get_queryset(self):
        return LogSync.objects.filter(
            connexion__pharmacie_id=self.kwargs["pharmacie_id"],
            connexion__pharmacie__pharmacien=self.request.user,
        ).order_by("-date_sync")


# ─────────────────────────────────────────────────────────────────────────────
# ADMIN — SUPERVISION GLOBALE
# ─────────────────────────────────────────────────────────────────────────────

class AdminConnexionsListView(generics.ListAPIView):
    """GET /api/v1/lgo/admin/connexions/

    Liste toutes les connexions LGO — super admin uniquement.
    Filtres : ?statut=erreur  ?type_lgo=pharmagest
    """
    serializer_class   = ConnexionLGOSerializer
    permission_classes = [IsSuperAdmin]

    def get_queryset(self):
        qs = ConnexionLGO.objects.all().select_related("pharmacie")
        statut   = self.request.query_params.get("statut")
        type_lgo = self.request.query_params.get("type_lgo")
        if statut:
            qs = qs.filter(statut=statut)
        if type_lgo:
            qs = qs.filter(type_lgo=type_lgo)
        return qs.order_by("-updated_at")


class AdminStatsView(APIView):
    """GET /api/v1/lgo/admin/stats/

    Statistiques globales des synchronisations — dashboard super admin.
    """
    permission_classes = [IsSuperAdmin]

    def get(self, request):
        from datetime import timedelta
        from django.db.models import Count

        aujourd_hui   = timezone.now().date()
        il_y_a_7_jours = timezone.now() - timedelta(days=7)

        stats = {
            "total_connexions":     ConnexionLGO.objects.count(),
            "connexions_actives":   ConnexionLGO.objects.filter(statut="active").count(),
            "connexions_en_erreur": ConnexionLGO.objects.filter(statut="erreur").count(),
            "syncs_aujourd_hui":    LogSync.objects.filter(
                date_sync__date=aujourd_hui
            ).count(),
            "syncs_succes_7j":      LogSync.objects.filter(
                date_sync__gte=il_y_a_7_jours, resultat="succes"
            ).count(),
            "syncs_echec_7j":       LogSync.objects.filter(
                date_sync__gte=il_y_a_7_jours, resultat="echec"
            ).count(),
        }

        serializer = StatsSyncSerializer(stats)
        return Response(serializer.data)