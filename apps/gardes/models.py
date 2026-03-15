# apps/gardes/models.py
from django.db import models
from django.utils import timezone
from apps.pharmacies.models import Pharmacie


class PeriodeGarde(models.Model):
    """Période de garde déclarée par une pharmacie.

    Une garde est une plage horaire durant laquelle la pharmacie
    assure un service d'urgence, souvent en dehors des horaires normaux.

    Workflow :
        1. Pharmacien déclare une période → statut PLANIFIEE
        2. Celery Beat détecte que la garde commence → statut EN_COURS
                                                     → est_de_garde=True sur Pharmacie
        3. Celery Beat détecte que la garde termine  → statut TERMINEE
                                                     → est_de_garde=False sur Pharmacie

    Attributes:
        pharmacie:        Pharmacie assurant la garde
        date_debut:       Début de la période de garde
        date_fin:         Fin de la période de garde
        telephone_garde:  Numéro dédié pendant la garde (peut différer du numéro habituel)
        zone_ville:       Ville couverte par la garde
        zone_quartier:    Quartier ou zone spécifique (optionnel)
        statut:           PLANIFIEE | EN_COURS | TERMINEE | ANNULEE
        note:             Note libre (ex: "Garde de nuit de la fête nationale")
        created_at:       Date de déclaration
    """

    class Statut(models.TextChoices):
        PLANIFIEE = "planifiee", "Planifiée"
        EN_COURS  = "en_cours",  "En cours"
        TERMINEE  = "terminee",  "Terminée"
        ANNULEE   = "annulee",   "Annulée"

    # ── Relations ─────────────────────────────────────────────────────────────
    pharmacie = models.ForeignKey(
        Pharmacie,
        on_delete=models.CASCADE,
        related_name="periodes_garde",
        verbose_name="Pharmacie",
    )

    # ── Plage horaire ─────────────────────────────────────────────────────────
    date_debut = models.DateTimeField(verbose_name="Début de garde")
    date_fin   = models.DateTimeField(verbose_name="Fin de garde")

    # ── Contact ───────────────────────────────────────────────────────────────
    telephone_garde = models.CharField(
        max_length=20,
        blank=True,
        default="",
        verbose_name="Téléphone de garde",
        help_text="Numéro dédié pendant la garde. Si vide, le numéro de la pharmacie est utilisé.",
    )

    # ── Zone géographique ─────────────────────────────────────────────────────
    zone_ville = models.CharField(
        max_length=100,
        blank=True,
        default="",
        verbose_name="Ville couverte",
        help_text="Ville ou commune couverte par cette garde.",
    )
    zone_quartier = models.CharField(
        max_length=100,
        blank=True,
        default="",
        verbose_name="Quartier / Zone",
        help_text="Quartier ou zone précise (optionnel).",
    )

    # ── Statut & infos ────────────────────────────────────────────────────────
    statut = models.CharField(
        max_length=20,
        choices=Statut.choices,
        default=Statut.PLANIFIEE,
        verbose_name="Statut",
    )
    note = models.CharField(
        max_length=255,
        blank=True,
        default="",
        verbose_name="Note",
        help_text="Information complémentaire sur cette garde.",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering            = ["date_debut"]
        verbose_name        = "Période de garde"
        verbose_name_plural = "Périodes de garde"
        indexes = [
            models.Index(fields=["statut"],     name="idx_garde_statut"),
            models.Index(fields=["date_debut"], name="idx_garde_debut"),
            models.Index(fields=["date_fin"],   name="idx_garde_fin"),
            models.Index(fields=["zone_ville"], name="idx_garde_ville"),
        ]

    def __str__(self) -> str:
        debut = self.date_debut.strftime("%d/%m/%Y %H:%M")
        fin   = self.date_fin.strftime("%d/%m/%Y %H:%M")
        return f"{self.pharmacie.nom} — {debut} → {fin} [{self.get_statut_display()}]"

    # ── Propriétés ────────────────────────────────────────────────────────────
    @property
    def est_active_maintenant(self) -> bool:
        """True si la garde est en cours à l'instant présent."""
        maintenant = timezone.now()
        return self.date_debut <= maintenant <= self.date_fin

    @property
    def telephone_effectif(self) -> str:
        """Retourne le téléphone de garde ou celui de la pharmacie par défaut."""
        return self.telephone_garde or self.pharmacie.telephone

    @property
    def est_passee(self) -> bool:
        """True si la garde est terminée."""
        return timezone.now() > self.date_fin

    @property
    def est_a_venir(self) -> bool:
        """True si la garde n'a pas encore commencé."""
        return timezone.now() < self.date_debut

    # ── Méthodes métier ───────────────────────────────────────────────────────
    def activer(self) -> None:
        """Passe la garde en statut EN_COURS et met à jour la pharmacie."""
        self.statut = self.Statut.EN_COURS
        self.save(update_fields=["statut"])
        self.pharmacie.est_de_garde = True
        self.pharmacie.save(update_fields=["est_de_garde"])

    def terminer(self) -> None:
        """Passe la garde en statut TERMINEE et met à jour la pharmacie si
        aucune autre garde n'est active pour cette pharmacie.
        """
        self.statut = self.Statut.TERMINEE
        self.save(update_fields=["statut"])

        # Vérifie si une autre garde est toujours active pour cette pharmacie
        garde_active = PeriodeGarde.objects.filter(
            pharmacie=self.pharmacie,
            statut=self.Statut.EN_COURS,
        ).exclude(pk=self.pk).exists()

        if not garde_active:
            self.pharmacie.est_de_garde = False
            self.pharmacie.save(update_fields=["est_de_garde"])

    def annuler(self) -> None:
        """Annule la garde."""
        self.statut = self.Statut.ANNULEE
        self.save(update_fields=["statut"])
        # Recalcule est_de_garde
        self.terminer.__wrapped__ if hasattr(self.terminer, '__wrapped__') else None
        garde_active = PeriodeGarde.objects.filter(
            pharmacie=self.pharmacie,
            statut=self.Statut.EN_COURS,
        ).exists()
        if not garde_active:
            self.pharmacie.est_de_garde = False
            self.pharmacie.save(update_fields=["est_de_garde"])