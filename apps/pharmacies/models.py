# apps/pharmacies/models.py
from django.db import models
from django.conf import settings

# PointField PostGIS uniquement disponible si USE_POSTGIS=True
# En dev Windows (USE_POSTGIS=False) : on utilise lat/lng décimaux uniquement
_USE_POSTGIS = getattr(settings, "USE_POSTGIS", False)
if _USE_POSTGIS:
    from django.contrib.gis.db import models as gis_models


def logo_upload_path(instance, filename):
    """Chemin d'upload du logo : logos/pharmacie_<id>/<filename>"""
    return f"logos/pharmacie_{instance.pk}/{filename}"


class Pharmacie(models.Model):
    """Officine enregistrée sur la plateforme PharmaLink.

    Workflow :
        1. Pharmacien crée sa pharmacie → statut EN_ATTENTE
        2. Super admin valide          → statut ACTIVE
        3. Super admin peut suspendre  → statut SUSPENDUE

    Géolocalisation :
        - latitude/longitude : champs décimaux simples (dev + prod)
        - localisation : PointField PostGIS pour les requêtes spatiales (prod)
        Les deux sont maintenus en sync via la méthode save().

    Attributes:
        pharmacien:       Gérant responsable (ForeignKey → CustomUser)
        nom:              Nom commercial de l'officine
        numero_agrement:  Numéro d'agrément délivré par l'autorité béninoise
        siret:            Numéro SIRET (optionnel, contexte international)
        adresse:          Adresse complète
        ville:            Ville
        code_postal:      Code postal
        telephone:        Numéro de téléphone principal
        email:            Email de contact
        site_web:         Site web (optionnel)
        description:      Présentation libre de l'officine
        logo:             Photo / logo de la pharmacie
        services:         Services proposés (JSON — liste de chaînes)
        latitude:         Latitude décimale
        longitude:        Longitude décimale
        localisation:     Point géospatial PostGIS (srid=4326)
        statut:           EN_ATTENTE | ACTIVE | SUSPENDUE
        est_ouverte:      Calculé dynamiquement depuis les horaires
        est_de_garde:     True si une PeriodeGarde est active
        created_at:       Date de création
        updated_at:       Date de dernière modification
    """

    class Statut(models.TextChoices):
        EN_ATTENTE = "en_attente", "En attente d'approbation"
        ACTIVE     = "active",     "Active"
        SUSPENDUE  = "suspendue",  "Suspendue"

    # ── Propriétaire ──────────────────────────────────────────────────────────
    pharmacien = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="pharmacies",
        limit_choices_to={"role": "pharmacien"},
        verbose_name="Pharmacien",
    )

    # ── Informations générales ────────────────────────────────────────────────
    nom = models.CharField(
        max_length=255,
        verbose_name="Nom de la pharmacie",
    )
    numero_agrement = models.CharField(
        max_length=50,
        blank=True,
        default="",
        verbose_name="Numéro d'agrément",
        help_text="Numéro d'agrément délivré par le Ministère de la Santé du Bénin.",
    )
    siret = models.CharField(
        max_length=20,
        blank=True,
        default="",
        verbose_name="SIRET / Registre commerce",
    )
    description = models.TextField(
        blank=True,
        default="",
        verbose_name="Description",
        help_text="Présentation libre de l'officine (spécialités, équipe, historique...).",
    )
    logo = models.ImageField(
        upload_to=logo_upload_path,
        null=True,
        blank=True,
        verbose_name="Logo / Photo",
    )

    # ── Services proposés ─────────────────────────────────────────────────────
    # Stocké en JSON : ["livraison", "urgences", "vaccins", "garde_nuit"]
    # Choix prédéfinis côté serializer pour la cohérence
    services = models.JSONField(
        default=list,
        blank=True,
        verbose_name="Services",
        help_text='Ex: ["livraison", "urgences", "vaccins", "bebe", "dermatologie"]',
    )

    # ── Coordonnées ───────────────────────────────────────────────────────────
    adresse     = models.CharField(max_length=500, verbose_name="Adresse")
    ville       = models.CharField(max_length=100, verbose_name="Ville")
    code_postal = models.CharField(max_length=10, blank=True, default="", verbose_name="Code postal")
    telephone   = models.CharField(max_length=20, blank=True, default="", verbose_name="Téléphone")
    email       = models.EmailField(blank=True, default="", verbose_name="Email")
    site_web    = models.URLField(blank=True, default="", verbose_name="Site web")

    # ── Géolocalisation ───────────────────────────────────────────────────────
    latitude     = models.DecimalField(
        max_digits=9, decimal_places=6,
        null=True, blank=True,
        verbose_name="Latitude",
    )
    longitude    = models.DecimalField(
        max_digits=9, decimal_places=6,
        null=True, blank=True,
        verbose_name="Longitude",
    )
    # PointField PostGIS — utilisé pour les requêtes spatiales (distance, rayon)
    # Uniquement en production avec PostGIS. En dev : lat/lng décimaux suffisent.
    localisation = (
        gis_models.PointField(
            null=True, blank=True,
            srid=4326,
            geography=True,
            verbose_name="Localisation (PostGIS)",
        )
        if _USE_POSTGIS
        else models.BinaryField(null=True, blank=True, editable=False)
    )

    # ── Statut ────────────────────────────────────────────────────────────────
    statut       = models.CharField(
        max_length=20,
        choices=Statut.choices,
        default=Statut.EN_ATTENTE,
        verbose_name="Statut",
    )
    est_ouverte  = models.BooleanField(
        default=False,
        verbose_name="Est ouverte",
        help_text="Mis à jour dynamiquement selon les horaires.",
    )
    est_de_garde = models.BooleanField(
        default=False,
        verbose_name="De garde",
        help_text="Mis à jour dynamiquement selon les périodes de garde.",
    )

    # ── Métadonnées ───────────────────────────────────────────────────────────
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering         = ["nom"]
        verbose_name     = "Pharmacie"
        verbose_name_plural = "Pharmacies"
        indexes = [
            models.Index(fields=["statut"],       name="idx_pharmacie_statut"),
            models.Index(fields=["ville"],        name="idx_pharmacie_ville"),
            models.Index(fields=["est_ouverte"],  name="idx_pharmacie_ouverte"),
            models.Index(fields=["est_de_garde"], name="idx_pharmacie_garde"),
        ]

    def __str__(self) -> str:
        return f"{self.nom} — {self.ville} [{self.get_statut_display()}]"

    # ── Save : synchronisation lat/lng ↔ PointField ───────────────────────────
    def save(self, *args, **kwargs):
        """Synchronise latitude/longitude vers le PointField PostGIS (prod uniquement)."""
        if _USE_POSTGIS and self.latitude and self.longitude:
            from django.contrib.gis.geos import Point
            self.localisation = Point(
                float(self.longitude),
                float(self.latitude),
                srid=4326,
            )
        super().save(*args, **kwargs)

    # ── Propriétés utilitaires ────────────────────────────────────────────────
    @property
    def est_active(self) -> bool:
        """True si la pharmacie est active (approuvée)."""
        return self.statut == self.Statut.ACTIVE

    @property
    def coordonnees(self) -> dict | None:
        """Retourne les coordonnées sous forme de dict."""
        if self.latitude and self.longitude:
            return {"lat": float(self.latitude), "lng": float(self.longitude)}
        return None

    # ── Méthodes métier ───────────────────────────────────────────────────────
    def activer(self, admin) -> None:
        """Active la pharmacie (approbation super admin).

        Args:
            admin: Super admin effectuant l'activation.
        """
        self.statut = self.Statut.ACTIVE
        self.save(update_fields=["statut", "updated_at"])

    def suspendre(self, raison: str = "") -> None:
        """Suspend la pharmacie.

        Args:
            raison: Motif de la suspension (pour les logs).
        """
        self.statut = self.Statut.SUSPENDUE
        self.save(update_fields=["statut", "updated_at"])