# apps/connecteurs_lgo/tasks.py
import logging
import time
from celery import shared_task
from django.utils import timezone

# Imports au niveau module → patchables dans les tests
from .pharmagest import ConnecteurPharmagest
from .winpharma  import ConnecteurWinpharma

logger = logging.getLogger(__name__)

CONNECTEURS = {
    "pharmagest": ConnecteurPharmagest,
    "winpharma":  ConnecteurWinpharma,
}


@shared_task(bind=True, max_retries=3)
def sync_pharmacie_lgo(self, pharmacie_id: int, declenchement: str = "auto") -> dict:
    """Synchronise une pharmacie avec son LGO."""
    from .models import ConnexionLGO, LogSync

    try:
        connexion = ConnexionLGO.objects.select_related("pharmacie").get(
            pharmacie_id=pharmacie_id,
            statut="active",
        )
    except ConnexionLGO.DoesNotExist:
        logger.warning(f"Aucune connexion LGO active pour la pharmacie {pharmacie_id}")
        return {"status": "skipped"}

    ConnecteurClass = CONNECTEURS.get(connexion.type_lgo)
    if not ConnecteurClass:
        logger.error(f"Connecteur inconnu : {connexion.type_lgo}")
        return {"status": "error", "message": "Type LGO non supporté"}

    debut = time.time()
    try:
        connecteur = ConnecteurClass(connexion.config)
        stats      = connecteur.synchroniser(pharmacie_id, declenchement)

        LogSync.objects.create(
            connexion=connexion,
            resultat="succes" if not stats["erreurs"] else "partiel",
            declenchement=declenchement,
            produits_sync=stats["produits"],
            stocks_sync=stats["stocks"],
            prix_sync=stats["prix"],
            duree_secondes=stats["duree"],
            message_erreur="\n".join(stats["erreurs"]),
        )

        connexion.marquer_succes()
        logger.info(f"Sync OK — pharmacie {pharmacie_id} : {stats['produits']} produits")
        return {"status": "ok", **stats}

    except Exception as exc:
        duree = round(time.time() - debut, 2)
        LogSync.objects.create(
            connexion=connexion,
            resultat="echec",
            declenchement=declenchement,
            duree_secondes=duree,
            message_erreur=str(exc),
        )
        connexion.marquer_erreur(str(exc))
        logger.error(f"Sync ECHEC — pharmacie {pharmacie_id} : {exc}")
        raise self.retry(exc=exc, countdown=300)


@shared_task
def sync_toutes_pharmacies() -> dict:
    """Lance la synchronisation de toutes les pharmacies actives (toutes les 30 min)."""
    from .models import ConnexionLGO

    connexions = ConnexionLGO.objects.filter(
        statut="active"
    ).values_list("pharmacie_id", flat=True)

    count = 0
    for pharmacie_id in connexions:
        sync_pharmacie_lgo.apply_async(
            args=[pharmacie_id, "auto"],
            queue="high",
            countdown=count * 2,
        )
        count += 1

    logger.info(f"Sync planifiée déclenchée pour {count} pharmacies")
    return {"pharmacies_declenchees": count}


@shared_task
def mise_a_jour_statut_gardes() -> dict:
    """Met à jour le statut des gardes toutes les 15 minutes."""
    from apps.gardes.models import PeriodeGarde

    maintenant = timezone.now()
    stats      = {"activees": 0, "terminees": 0}

    for garde in PeriodeGarde.objects.filter(
        statut=PeriodeGarde.Statut.PLANIFIEE,
        date_debut__lte=maintenant,
        date_fin__gte=maintenant,
    ).select_related("pharmacie"):
        garde.activer()
        stats["activees"] += 1
        logger.info(f"Garde activée : {garde.pharmacie.nom}")

    for garde in PeriodeGarde.objects.filter(
        statut=PeriodeGarde.Statut.EN_COURS,
        date_fin__lt=maintenant,
    ).select_related("pharmacie"):
        garde.terminer()
        stats["terminees"] += 1
        logger.info(f"Garde terminée : {garde.pharmacie.nom}")

    logger.info(f"MAJ gardes — {stats['activees']} activée(s), {stats['terminees']} terminée(s)")
    return stats


@shared_task
def mise_a_jour_statut_ouverture() -> dict:
    """Met à jour est_ouverte de toutes les pharmacies actives toutes les 15 min."""
    from apps.pharmacies.models import Pharmacie
    from apps.horaires.models import est_ouverte_maintenant

    pharmacies   = Pharmacie.objects.filter(statut="active")
    mises_a_jour = 0

    for pharmacie in pharmacies:
        nouvelle_valeur = est_ouverte_maintenant(pharmacie)
        if pharmacie.est_ouverte != nouvelle_valeur:
            pharmacie.est_ouverte = nouvelle_valeur
            pharmacie.save(update_fields=["est_ouverte"])
            mises_a_jour += 1

    logger.info(f"Ouverture MAJ — {mises_a_jour}/{pharmacies.count()} pharmacies modifiées")
    return {"pharmacies_mises_a_jour": mises_a_jour, "total": pharmacies.count()}


@shared_task
def nettoyer_vieux_logs(jours_retention: int = 30) -> dict:
    """Supprime les logs de sync de plus de jours_retention jours."""
    from datetime import timedelta
    from .models import LogSync

    date_limite = timezone.now() - timedelta(days=jours_retention)
    count, _    = LogSync.objects.filter(date_sync__lt=date_limite).delete()

    logger.info(f"Nettoyage logs — {count} entrées supprimées (avant {date_limite.date()})")
    return {"logs_supprimes": count, "date_limite": str(date_limite.date())}