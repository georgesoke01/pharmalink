# apps/connecteurs_lgo/models.py
from django.db import models
from apps.pharmacies.models import Pharmacie


class ConnexionLGO(models.Model):
    """Configuration de la connexion au LGO d'une pharmacie.

    La config JSON est générée AUTOMATIQUEMENT par l'app Desktop Tauri
    lors de la détection du LGO sur le poste — jamais saisie manuellement.

    Workflow auto-détection :
        1. App Desktop Tauri scanne le poste (registre Windows, chemins standards)
        2. Détecte le LGO installé et son chemin de base de données
        3. Demande autorisation à l'utilisateur
        4. Envoie POST /api/v1/lgo/detection/ avec la config générée
        5. Django crée cette ConnexionLGO et déclenche la première sync

    Security :
        - Accès LGO : LECTURE SEULE — jamais d'écriture dans le LGO source
        - config JSON chiffré en production via django-encrypted-fields

    Attributes:
        pharmacie:          Pharmacie concernée (OneToOne)
        type_lgo:           LGO détecté (pharmagest | winpharma | lgpi | smart_rx)
        config:             Paramètres de connexion générés automatiquement
        statut:             INACTIVE | ACTIVE | ERREUR
        version_lgo:        Version du LGO détectée sur le poste
        poste_nom:          Nom du poste Windows où le LGO est installé
        detecte_auto:       True si détecté automatiquement par Tauri
        derniere_sync:      Date de la dernière synchronisation réussie
        nb_syncs_ok:        Compteur de synchronisations réussies
        nb_syncs_erreur:    Compteur de synchronisations en erreur
    """

    class TypeLGO(models.TextChoices):
        PHARMAGEST = "pharmagest", "Pharmagest"
        WINPHARMA  = "winpharma",  "Winpharma"
        LGPI       = "lgpi",       "LGPI"
        SMART_RX   = "smart_rx",   "Smart Rx"
        AUTRE      = "autre",      "Autre"

    class Statut(models.TextChoices):
        INACTIVE = "inactive", "Inactive"
        ACTIVE   = "active",   "Active"
        ERREUR   = "erreur",   "En erreur"

    # ── Relations ─────────────────────────────────────────────────────────────
    pharmacie = models.OneToOneField(
        Pharmacie,
        on_delete=models.CASCADE,
        related_name="connexion_lgo",
        verbose_name="Pharmacie",
    )

    # ── Identification du LGO ─────────────────────────────────────────────────
    type_lgo = models.CharField(
        max_length=20,
        choices=TypeLGO.choices,
        verbose_name="Type de LGO",
    )
    version_lgo = models.CharField(
        max_length=50,
        blank=True,
        default="",
        verbose_name="Version LGO",
        help_text="Version du LGO détectée sur le poste (ex: 8.2.1).",
    )
    poste_nom = models.CharField(
        max_length=100,
        blank=True,
        default="",
        verbose_name="Nom du poste",
        help_text="Nom du poste Windows où le LGO est installé.",
    )

    # ── Config générée automatiquement par Tauri ──────────────────────────────
    # Structure type :
    # {
    #   "db_path": "C:\\Pharmagest\\Data\\pharma.db",
    #   "db_type": "sqlite",          # sqlite | mysql | sqlserver
    #   "db_host": null,              # si MySQL distant
    #   "db_port": null,
    #   "db_name": null,
    #   "detecte_automatiquement": true,
    #   "chemin_installation": "C:\\Pharmagest\\"
    # }
    config = models.JSONField(
        default=dict,
        verbose_name="Configuration",
        help_text="Générée automatiquement par l'app Desktop. Ne pas modifier manuellement.",
    )
    detecte_auto = models.BooleanField(
        default=False,
        verbose_name="Détecté automatiquement",
        help_text="True si la config a été générée par l'auto-détection Tauri.",
    )

    # ── Statut & métriques ────────────────────────────────────────────────────
    statut = models.CharField(
        max_length=20,
        choices=Statut.choices,
        default=Statut.INACTIVE,
        verbose_name="Statut",
    )
    derniere_sync    = models.DateTimeField(null=True, blank=True, verbose_name="Dernière sync")
    nb_syncs_ok      = models.PositiveIntegerField(default=0, verbose_name="Syncs réussies")
    nb_syncs_erreur  = models.PositiveIntegerField(default=0, verbose_name="Syncs en erreur")
    derniere_erreur  = models.TextField(blank=True, default="", verbose_name="Dernière erreur")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name     = "Connexion LGO"
        verbose_name_plural = "Connexions LGO"

    def __str__(self) -> str:
        return f"{self.pharmacie.nom} → {self.get_type_lgo_display()} [{self.get_statut_display()}]"

    # ── Méthodes métier ───────────────────────────────────────────────────────
    def marquer_succes(self) -> None:
        """Met à jour les métriques après une sync réussie."""
        from django.utils import timezone
        self.statut         = self.Statut.ACTIVE
        self.derniere_sync  = timezone.now()
        self.nb_syncs_ok   += 1
        self.derniere_erreur = ""
        self.save(update_fields=[
            "statut", "derniere_sync", "nb_syncs_ok",
            "derniere_erreur", "updated_at",
        ])

    def marquer_erreur(self, message: str) -> None:
        """Met à jour les métriques après une sync échouée."""
        self.statut          = self.Statut.ERREUR
        self.nb_syncs_erreur += 1
        self.derniere_erreur  = message
        self.save(update_fields=[
            "statut", "nb_syncs_erreur", "derniere_erreur", "updated_at",
        ])

    @property
    def taux_succes(self) -> float:
        """Taux de succès des synchronisations (0.0 à 1.0)."""
        total = self.nb_syncs_ok + self.nb_syncs_erreur
        return round(self.nb_syncs_ok / total, 2) if total > 0 else 0.0


class LogSync(models.Model):
    """Journal détaillé de chaque synchronisation LGO → API PharmaLink.

    Conservé 30 jours puis purgé automatiquement par Celery Beat.

    Attributes:
        connexion:       ConnexionLGO concernée
        date_sync:       Date/heure de la synchronisation
        resultat:        SUCCES | PARTIEL | ECHEC
        declenchement:   AUTO (Celery) | MANUEL (pharmacien) | INSTALLATION (première sync)
        produits_sync:   Nombre de produits synchronisés
        stocks_sync:     Nombre de stocks mis à jour
        prix_sync:       Nombre de prix mis à jour
        duree_secondes:  Durée totale de la sync
        message_erreur:  Détail des erreurs si PARTIEL ou ECHEC
    """

    class Resultat(models.TextChoices):
        SUCCES  = "succes",  "Succès"
        PARTIEL = "partiel", "Partiel (avec erreurs)"
        ECHEC   = "echec",   "Échec"

    class Declenchement(models.TextChoices):
        AUTO         = "auto",         "Automatique (Celery)"
        MANUEL       = "manuel",       "Manuel (pharmacien)"
        INSTALLATION = "installation", "Première sync (installation)"

    connexion = models.ForeignKey(
        ConnexionLGO,
        on_delete=models.CASCADE,
        related_name="logs",
        verbose_name="Connexion LGO",
    )
    date_sync        = models.DateTimeField(auto_now_add=True)
    resultat         = models.CharField(max_length=10, choices=Resultat.choices)
    declenchement    = models.CharField(
        max_length=20,
        choices=Declenchement.choices,
        default=Declenchement.AUTO,
    )
    produits_sync    = models.PositiveIntegerField(default=0)
    stocks_sync      = models.PositiveIntegerField(default=0)
    prix_sync        = models.PositiveIntegerField(default=0)
    duree_secondes   = models.FloatField(default=0)
    message_erreur   = models.TextField(blank=True, default="")

    class Meta:
        ordering            = ["-date_sync"]
        verbose_name        = "Log de synchronisation"
        verbose_name_plural = "Logs de synchronisation"
        indexes = [
            models.Index(fields=["resultat"],      name="idx_log_resultat"),
            models.Index(fields=["declenchement"], name="idx_log_declenchement"),
        ]

    def __str__(self) -> str:
        return (
            f"{self.connexion.pharmacie.nom} — "
            f"{self.date_sync.strftime('%d/%m/%Y %H:%M')} "
            f"[{self.get_resultat_display()}]"
        )