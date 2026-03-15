# apps/produits/models.py
from django.db import models
from apps.pharmacies.models import Pharmacie


def produit_image_path(instance, filename):
    """Chemin d'upload : produits/images/<code_cip13>/<filename>"""
    code = instance.code_cip13 or "sans_code"
    return f"produits/images/{code}/{filename}"


class Produit(models.Model):
    """Produit du catalogue global PharmaLink.

    Un produit est une entité globale (partagée entre toutes les pharmacies).
    Le stock et le prix sont propres à chaque pharmacie (modèles Stock et Prix).

    Note:
        sur_ordonnance=True → pictogramme dédié dans l'app mobile.
        Le code CIP13 est le code national français d'identification
        des médicaments. Dans le contexte béninois, il peut être remplacé
        par un code local ou laissé vide.

    Attributes:
        code_cip13:         Code CIP13 (identifiant national médicament)
        nom:                Nom commercial
        nom_generique:      Dénomination commune internationale (DCI)
        laboratoire:        Fabricant / laboratoire
        categorie:          MEDICAMENT | PARAPHARMACIE | MATERIEL | AUTRE
        forme:              Forme pharmaceutique (comprimé, sirop, injection...)
        dosage:             Dosage (ex: 500mg, 250mg/5ml)
        sur_ordonnance:     Médicament soumis à prescription
        contre_indications: Contre-indications principales
        description:        Description libre
        image:              Photo du produit
        created_at:         Date de création
        updated_at:         Date de dernière modification
    """

    class Categorie(models.TextChoices):
        MEDICAMENT    = "medicament",    "Médicament"
        PARAPHARMACIE = "parapharmacie", "Parapharmacie"
        MATERIEL      = "materiel",      "Matériel médical"
        AUTRE         = "autre",         "Autre"

    class Forme(models.TextChoices):
        COMPRIMES   = "comprimes",   "Comprimés"
        GELULES     = "gelules",     "Gélules"
        SIROP       = "sirop",       "Sirop"
        INJECTION   = "injection",   "Injectable"
        CREME       = "creme",       "Crème / Pommade"
        GOUTTES     = "gouttes",     "Gouttes"
        SUPPOSITOIRE = "suppositoire", "Suppositoire"
        SACHET      = "sachet",      "Sachet"
        SPRAY       = "spray",       "Spray"
        AUTRE       = "autre",       "Autre"

    # ── Identification ────────────────────────────────────────────────────────
    code_cip13 = models.CharField(
        max_length=13,
        blank=True,
        default="",
        db_index=True,
        verbose_name="Code CIP13",
        help_text="Code national d'identification du médicament (13 chiffres).",
    )
    nom = models.CharField(
        max_length=500,
        verbose_name="Nom commercial",
    )
    nom_generique = models.CharField(
        max_length=500,
        blank=True,
        default="",
        verbose_name="Nom générique (DCI)",
    )
    laboratoire = models.CharField(
        max_length=255,
        blank=True,
        default="",
        verbose_name="Laboratoire",
    )

    # ── Classification ────────────────────────────────────────────────────────
    categorie = models.CharField(
        max_length=20,
        choices=Categorie.choices,
        default=Categorie.MEDICAMENT,
        verbose_name="Catégorie",
    )
    forme = models.CharField(
        max_length=20,
        choices=Forme.choices,
        blank=True,
        default="",
        verbose_name="Forme pharmaceutique",
    )
    dosage = models.CharField(
        max_length=100,
        blank=True,
        default="",
        verbose_name="Dosage",
        help_text="Ex: 500mg, 250mg/5ml, 1000UI",
    )
    sur_ordonnance = models.BooleanField(
        default=False,
        verbose_name="Sur ordonnance",
        help_text="Si True, un pictogramme dédié s'affiche dans l'app mobile.",
    )

    # ── Informations médicales ────────────────────────────────────────────────
    contre_indications = models.TextField(
        blank=True,
        default="",
        verbose_name="Contre-indications",
        help_text="Principales contre-indications à afficher dans la fiche produit.",
    )
    description = models.TextField(
        blank=True,
        default="",
        verbose_name="Description",
    )

    # ── Image ─────────────────────────────────────────────────────────────────
    image = models.ImageField(
        upload_to=produit_image_path,
        null=True,
        blank=True,
        verbose_name="Image du produit",
    )

    # ── Métadonnées ───────────────────────────────────────────────────────────
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering         = ["nom"]
        verbose_name     = "Produit"
        verbose_name_plural = "Produits"
        indexes = [
            models.Index(fields=["categorie"],      name="idx_produit_categorie"),
            models.Index(fields=["sur_ordonnance"], name="idx_produit_ordonnance"),
            models.Index(fields=["laboratoire"],    name="idx_produit_labo"),
        ]

    def __str__(self) -> str:
        mention = " 📋" if self.sur_ordonnance else ""
        dosage  = f" {self.dosage}" if self.dosage else ""
        return f"{self.nom}{dosage}{mention}"


class Stock(models.Model):
    """Niveau de stock d'un produit dans une pharmacie spécifique.

    Le seuil_alerte permet de détecter les stocks bas et d'alerter
    le pharmacien via une tâche Celery.

    Attributes:
        pharmacie:      Pharmacie concernée
        produit:        Produit concerné
        quantite:       Quantité disponible en unités
        disponible:     False si rupture de stock complète
        seuil_alerte:   Quantité minimale avant alerte stock bas (0 = désactivé)
        updated_at:     Date de dernière mise à jour du stock
    """

    pharmacie = models.ForeignKey(
        Pharmacie,
        on_delete=models.CASCADE,
        related_name="stocks",
        verbose_name="Pharmacie",
    )
    produit = models.ForeignKey(
        Produit,
        on_delete=models.CASCADE,
        related_name="stocks",
        verbose_name="Produit",
    )
    quantite = models.PositiveIntegerField(
        default=0,
        verbose_name="Quantité",
    )
    disponible = models.BooleanField(
        default=True,
        verbose_name="Disponible",
        help_text="False = rupture de stock complète.",
    )
    seuil_alerte = models.PositiveIntegerField(
        default=0,
        verbose_name="Seuil d'alerte",
        help_text="Alerte envoyée quand quantite <= seuil. 0 = alerte désactivée.",
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together  = ("pharmacie", "produit")
        verbose_name     = "Stock"
        verbose_name_plural = "Stocks"
        indexes = [
            models.Index(fields=["disponible"], name="idx_stock_disponible"),
        ]

    def __str__(self) -> str:
        return f"{self.produit.nom} @ {self.pharmacie.nom} — {self.quantite} unités"

    # ── Propriétés ────────────────────────────────────────────────────────────
    @property
    def est_en_alerte(self) -> bool:
        """True si le stock est sous le seuil d'alerte."""
        return self.seuil_alerte > 0 and self.quantite <= self.seuil_alerte

    @property
    def est_en_rupture(self) -> bool:
        """True si le stock est épuisé."""
        return self.quantite == 0 or not self.disponible

    # ── Save : mise à jour automatique de disponible ──────────────────────────
    def save(self, *args, **kwargs):
        """Passe disponible=False automatiquement si quantite=0."""
        if self.quantite == 0:
            self.disponible = False
        super().save(*args, **kwargs)


class Prix(models.Model):
    """Prix de vente d'un produit dans une pharmacie (en FCFA).

    Attributes:
        pharmacie:   Pharmacie concernée
        produit:     Produit concerné
        prix_fcfa:   Prix de vente TTC en Franc CFA (XOF)
        updated_at:  Date de dernière mise à jour du prix
    """

    pharmacie = models.ForeignKey(
        Pharmacie,
        on_delete=models.CASCADE,
        related_name="prix",
        verbose_name="Pharmacie",
    )
    produit = models.ForeignKey(
        Produit,
        on_delete=models.CASCADE,
        related_name="prix",
        verbose_name="Produit",
    )
    prix_fcfa = models.PositiveIntegerField(
        verbose_name="Prix (FCFA)",
        help_text="Prix de vente TTC en Franc CFA (XOF). Ex: 2500",
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together  = ("pharmacie", "produit")
        verbose_name     = "Prix"
        verbose_name_plural = "Prix"

    def __str__(self) -> str:
        return f"{self.produit.nom} @ {self.pharmacie.nom} — {self.prix_fcfa:,} FCFA"