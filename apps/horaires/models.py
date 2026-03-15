# apps/horaires/models.py
from django.db import models
from django.utils import timezone
from apps.pharmacies.models import Pharmacie


class HoraireSemaine(models.Model):
    """Horaires hebdomadaires récurrents d'une pharmacie.

    Supporte une double plage horaire (matin + après-midi) pour les
    pharmacies qui ferment à la mi-journée.

    Exemples :
        Lundi ouvert toute la journée :
            heure_ouverture=08:00  heure_fermeture=20:00
            pause_debut=None       pause_fin=None

        Lundi avec pause midi :
            heure_ouverture=08:00  heure_fermeture=20:00
            pause_debut=12:30      pause_fin=14:30

        Dimanche fermé :
            est_ferme=True

    Attributes:
        pharmacie:       Pharmacie concernée
        jour:            0=Lundi … 6=Dimanche
        heure_ouverture: Heure d'ouverture du matin
        heure_fermeture: Heure de fermeture du soir
        pause_debut:     Début de la pause midi (optionnel)
        pause_fin:       Fin de la pause midi (optionnel)
        est_ferme:       True = fermé toute la journée
        updated_at:      Date de dernière modification
    """

    JOURS = [
        (0, "Lundi"), (1, "Mardi"), (2, "Mercredi"), (3, "Jeudi"),
        (4, "Vendredi"), (5, "Samedi"), (6, "Dimanche"),
    ]

    pharmacie = models.ForeignKey(
        Pharmacie,
        on_delete=models.CASCADE,
        related_name="horaires_semaine",
        verbose_name="Pharmacie",
    )
    jour = models.IntegerField(choices=JOURS, verbose_name="Jour")

    # ── Plage principale ──────────────────────────────────────────────────────
    heure_ouverture = models.TimeField(null=True, blank=True, verbose_name="Ouverture")
    heure_fermeture = models.TimeField(null=True, blank=True, verbose_name="Fermeture")

    # ── Pause midi (double plage) ─────────────────────────────────────────────
    pause_debut = models.TimeField(
        null=True, blank=True,
        verbose_name="Début pause midi",
        help_text="Laisser vide si ouverture continue.",
    )
    pause_fin = models.TimeField(
        null=True, blank=True,
        verbose_name="Fin pause midi",
        help_text="Laisser vide si ouverture continue.",
    )

    est_ferme  = models.BooleanField(default=False, verbose_name="Fermé")
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together     = ("pharmacie", "jour")
        ordering            = ["jour"]
        verbose_name        = "Horaire semaine"
        verbose_name_plural = "Horaires semaine"

    def __str__(self) -> str:
        if self.est_ferme:
            return f"{self.get_jour_display()} — Fermé"
        if self.pause_debut and self.pause_fin:
            return (
                f"{self.get_jour_display()} "
                f"{self.heure_ouverture}–{self.pause_debut} "
                f"/ {self.pause_fin}–{self.heure_fermeture}"
            )
        return f"{self.get_jour_display()} {self.heure_ouverture}–{self.heure_fermeture}"

    def est_ouvert_a(self, heure) -> bool:
        """Vérifie si la pharmacie est ouverte à une heure donnée ce jour.

        Args:
            heure: Objet datetime.time à tester.

        Returns:
            True si la pharmacie est ouverte à cette heure.
        """
        if self.est_ferme:
            return False
        if not self.heure_ouverture or not self.heure_fermeture:
            return False

        dans_plage = self.heure_ouverture <= heure <= self.heure_fermeture

        if dans_plage and self.pause_debut and self.pause_fin:
            en_pause = self.pause_debut <= heure <= self.pause_fin
            return not en_pause

        return dans_plage


class HoraireExceptionnel(models.Model):
    """Horaire exceptionnel pour un jour précis (férié, vacances, etc.).

    Prioritaire sur HoraireSemaine pour la date concernée.
    Supporte aussi la double plage (pause midi).

    Attributes:
        pharmacie:       Pharmacie concernée
        date:            Date précise concernée
        heure_ouverture: Heure d'ouverture (si ouvert)
        heure_fermeture: Heure de fermeture (si ouvert)
        pause_debut:     Début pause midi (optionnel)
        pause_fin:       Fin pause midi (optionnel)
        est_ferme:       True = fermé toute la journée ce jour
        motif:           Ex: "Fête nationale", "Congés annuels"
    """

    pharmacie       = models.ForeignKey(
        Pharmacie,
        on_delete=models.CASCADE,
        related_name="horaires_exceptionnels",
        verbose_name="Pharmacie",
    )
    date            = models.DateField(verbose_name="Date")
    heure_ouverture = models.TimeField(null=True, blank=True, verbose_name="Ouverture")
    heure_fermeture = models.TimeField(null=True, blank=True, verbose_name="Fermeture")
    pause_debut     = models.TimeField(null=True, blank=True, verbose_name="Début pause midi")
    pause_fin       = models.TimeField(null=True, blank=True, verbose_name="Fin pause midi")
    est_ferme       = models.BooleanField(default=True, verbose_name="Fermé")
    motif           = models.CharField(max_length=255, blank=True, default="", verbose_name="Motif")

    class Meta:
        unique_together     = ("pharmacie", "date")
        ordering            = ["date"]
        verbose_name        = "Horaire exceptionnel"
        verbose_name_plural = "Horaires exceptionnels"

    def __str__(self) -> str:
        statut = "Fermé" if self.est_ferme else "Ouvert"
        motif  = f" ({self.motif})" if self.motif else ""
        return f"{self.pharmacie.nom} — {self.date} [{statut}]{motif}"


# ─────────────────────────────────────────────────────────────────────────────
# FONCTION UTILITAIRE — est_ouverte_maintenant()
# ─────────────────────────────────────────────────────────────────────────────

def est_ouverte_maintenant(pharmacie: Pharmacie) -> bool:
    """Détermine si une pharmacie est ouverte à l'instant présent.

    Logique de priorité :
        1. Si un HoraireExceptionnel existe pour aujourd'hui → il prime
        2. Sinon, on consulte l'HoraireSemaine du jour courant

    Args:
        pharmacie: Instance de Pharmacie à vérifier.

    Returns:
        True si la pharmacie est ouverte maintenant.
    """
    maintenant  = timezone.localtime(timezone.now())
    aujourd_hui = maintenant.date()
    heure_now   = maintenant.time()

    # ── 1. Horaire exceptionnel (priorité maximale) ───────────────────────────
    try:
        excep = HoraireExceptionnel.objects.get(
            pharmacie=pharmacie,
            date=aujourd_hui,
        )
        if excep.est_ferme:
            return False
        if not excep.heure_ouverture or not excep.heure_fermeture:
            return False
        dans_plage = excep.heure_ouverture <= heure_now <= excep.heure_fermeture
        if dans_plage and excep.pause_debut and excep.pause_fin:
            return not (excep.pause_debut <= heure_now <= excep.pause_fin)
        return dans_plage

    except HoraireExceptionnel.DoesNotExist:
        pass

    # ── 2. Horaire hebdomadaire ───────────────────────────────────────────────
    # weekday() : 0=Lundi … 6=Dimanche (même convention que JOURS)
    try:
        horaire = HoraireSemaine.objects.get(
            pharmacie=pharmacie,
            jour=maintenant.weekday(),
        )
        return horaire.est_ouvert_a(heure_now)
    except HoraireSemaine.DoesNotExist:
        return False