# apps/connecteurs_lgo/tasks.py
import logging
import time
from celery import shared_task
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def sync_pharmacie_lgo(self, pharmacie_id: int) -> dict:
    """Synchronise une pharmacie avec son LGO.

    Args:
        pharmacie_id: ID de la pharmacie à synchroniser.

    Returns:
        Dictionnaire avec les stats de synchronisation.
    """
    from .models import ConnexionLGO, LogSync
    from .pharmagest import ConnecteurPharmagest
    from .winpharma import ConnecteurWinpharma

    CONNECTEURS = {
        "pharmagest": ConnecteurPharmagest,
        "winpharma":  ConnecteurWinpharma,
    }

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
        stats = connecteur.synchroniser(pharmacie_id)

        LogSync.objects.create(
            connexion=connexion,
            resultat="succes" if not stats["erreurs"] else "partiel",
            produits_sync=stats["produits"],
            stocks_sync=stats["stocks"],
            prix_sync=stats["prix"],
            duree_secondes=stats["duree"],
            message_erreur="\n".join(stats["erreurs"]),
        )

        connexion.derniere_sync = timezone.now()
        connexion.statut = "active"
        connexion.save(update_fields=["derniere_sync", "statut"])

        logger.info(f"Sync OK — pharmacie {pharmacie_id} : {stats['produits']} produits")
        return {"status": "ok", **stats}

    except Exception as exc:
        duree = round(time.time() - debut, 2)
        LogSync.objects.create(
            connexion=connexion,
            resultat="echec",
            duree_secondes=duree,
            message_erreur=str(exc),
        )
        connexion.statut = "erreur"
        connexion.save(update_fields=["statut"])

        logger.error(f"Sync ECHEC — pharmacie {pharmacie_id} : {exc}")
        raise self.retry(exc=exc, countdown=300)   # retry dans 5 minutes


@shared_task
def sync_toutes_pharmacies() -> dict:
    """Lance la synchronisation de toutes les pharmacies actives.

    Planifiée toutes les 30 minutes via Celery Beat.
    Chaque pharmacie est traitée dans une tâche indépendante (queue "high")
    pour ne pas bloquer les autres en cas d'échec isolé.
    """
    from .models import ConnexionLGO

    connexions = ConnexionLGO.objects.filter(
        statut="active"
    ).values_list("pharmacie_id", flat=True)

    count = 0
    for pharmacie_id in connexions:
        sync_pharmacie_lgo.apply_async(
            args=[pharmacie_id],
            queue="high",
            countdown=count * 2,   # échelonne les lancements (2s entre chaque)
                                    # évite le thundering herd sur le broker Redis
        )
        count += 1

    logger.info(f"Sync planifiée déclenchée pour {count} pharmacies")
    return {"pharmacies_declenchees": count}


@shared_task
def nettoyer_vieux_logs(jours_retention: int = 30) -> dict:
    """Supprime les anciens logs de synchronisation LGO.

    Planifiée chaque nuit à 2h via Celery Beat.
    Évite la croissance infinie de la table LogSync en base.

    Args:
        jours_retention: Nombre de jours de logs à conserver. Défaut : 30.

    Returns:
        Dictionnaire avec le nombre de logs supprimés.
    """
    from django.utils import timezone
    from datetime import timedelta
    from .models import LogSync

    date_limite = timezone.now() - timedelta(days=jours_retention)
    qs = LogSync.objects.filter(date_sync__lt=date_limite)
    count, _ = qs.delete()

    logger.info(
        f"Nettoyage logs LGO — {count} entrées supprimées "
        f"(antérieures au {date_limite.strftime('%Y-%m-%d')})"
    )
    return {"logs_supprimes": count, "date_limite": str(date_limite.date())}