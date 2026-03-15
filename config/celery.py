# config/celery.py
import os
import logging
from celery import Celery
from celery.schedules import crontab
from celery.signals import (
    task_failure,
    task_retry,
    worker_ready,
    worker_shutdown,
)

logger = logging.getLogger(__name__)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

# ── Initialisation de l'application Celery ────────────────────────────────────
app = Celery("pharmalink")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

# ── Configuration avancée ─────────────────────────────────────────────────────
app.conf.update(

    # ── Retry automatique des tâches échouées ─────────────────────────────────
    # Celery retente automatiquement les tâches qui lèvent une exception
    task_acks_late=True,              # Acquitte la tâche APRÈS exécution (pas avant)
                                      # → si le worker crash, la tâche sera relancée
    task_reject_on_worker_lost=True,  # Remet en queue si le worker est tué brutalement
    task_max_retries=3,               # 3 tentatives max avant abandon définitif

    # ── Expiration des tâches (timeout max) ───────────────────────────────────
    task_soft_time_limit=300,         # 5 min : lève SoftTimeLimitExceeded (gérable)
    task_time_limit=360,              # 6 min : kill brutal si toujours bloquée
                                      # → évite les tâches zombies qui saturent les workers

    # ── Fiabilité de la queue ─────────────────────────────────────────────────
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    result_expires=86400,             # Résultats conservés 24h dans Redis puis supprimés

    # ── Concurrence des workers ───────────────────────────────────────────────
    worker_prefetch_multiplier=1,     # 1 tâche à la fois par worker
                                      # → évite qu'un worker monopolise toutes les tâches LGO
    worker_max_tasks_per_child=100,   # Redémarre le process worker tous les 100 tâches
                                      # → prévient les fuites mémoire sur les connecteurs LGO

    # ── Priorité des queues ───────────────────────────────────────────────────
    # Queue "high" pour les syncs manuelles déclenchées par le pharmacien
    # Queue "default" pour les syncs automatiques planifiées
    task_routes={
        "apps.connecteurs_lgo.tasks.sync_pharmacie_lgo":    {"queue": "high"},
        "apps.connecteurs_lgo.tasks.sync_toutes_pharmacies": {"queue": "default"},
        "apps.connecteurs_lgo.tasks.nettoyer_vieux_logs":    {"queue": "default"},
    },
)

# ── Tâches planifiées (Celery Beat) ──────────────────────────────────────────
app.conf.beat_schedule = {

    # Sync LGO toutes les 30 minutes
    "sync-lgo-toutes-les-30min": {
        "task":     "apps.connecteurs_lgo.tasks.sync_toutes_pharmacies",
        "schedule": crontab(minute="0,30"),
        "options":  {"queue": "default"},
    },

    # Mise à jour statut ouverture toutes les 15 minutes
    "maj-statut-ouverture": {
        "task":     "apps.connecteurs_lgo.tasks.mise_a_jour_statut_ouverture",
        "schedule": crontab(minute="0,15,30,45"),
        "options":  {"queue": "default"},
    },

    # Mise à jour statut est_ouverte toutes les 15 minutes
    "maj-statuts-ouverture": {
        "task":     "apps.horaires.tasks.mettre_a_jour_statuts_ouverture",
        "schedule": crontab(minute="0,15,30,45"),
        "options":  {"queue": "default"},
    },

    # Nettoyage des anciens logs de sync — chaque nuit à 2h du matin
    "nettoyage-logs-sync-nuit": {
        "task":    "apps.connecteurs_lgo.tasks.nettoyer_vieux_logs",
        "schedule": crontab(hour=2, minute=0),
        "kwargs":  {"jours_retention": 30},   # supprime les logs > 30 jours
        "options": {"queue": "default"},
    },
}


# ── Signaux Celery — Monitoring & Logging ─────────────────────────────────────

@task_failure.connect
def on_task_failure(sender=None, task_id=None, exception=None, traceback=None, **kwargs):
    """Loggue chaque échec définitif de tâche (après tous les retries épuisés).
    Sentry capture automatiquement via l'intégration CeleryIntegration.
    """
    logger.error(
        f"[CELERY] Tâche échouée définitivement — "
        f"task={sender.name} id={task_id} erreur={exception}"
    )


@task_retry.connect
def on_task_retry(sender=None, reason=None, **kwargs):
    """Loggue chaque tentative de retry pour traçabilité."""
    logger.warning(
        f"[CELERY] Retry tâche — task={sender.name} raison={reason}"
    )


@worker_ready.connect
def on_worker_ready(sender=None, **kwargs):
    """Log au démarrage du worker — utile pour confirmer le démarrage en prod."""
    logger.info("[CELERY] Worker PharmaLink démarré et prêt.")


@worker_shutdown.connect
def on_worker_shutdown(sender=None, **kwargs):
    """Log à l'arrêt du worker."""
    logger.info("[CELERY] Worker PharmaLink arrêté proprement.")