# apps/users/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models

from .managers import CustomUserManager


def avatar_upload_path(instance, filename):
    """Génère le chemin d'upload de l'avatar : avatars/user_<id>/<filename>"""
    return f"avatars/user_{instance.pk}/{filename}"


class CustomUser(AbstractUser):
    """Utilisateur PharmaLink avec rôle étendu.

    Connexion possible via username OU email (géré par CustomUserManager).

    Roles:
        public      → utilisateur final mobile (lecture seule)
        pharmacien  → gérant d'officine (lecture/écriture sa pharmacie)
        super_admin → administrateur plateforme (accès complet)

    Workflow pharmacien :
        1. Inscription libre via l'API
        2. is_approved=False par défaut → accès bloqué
        3. Super admin approuve → is_approved=True → accès activé

    Attributes:
        role:             Rôle de l'utilisateur (public | pharmacien | super_admin)
        phone:            Numéro de téléphone (optionnel)
        avatar:           Photo de profil (optionnel)
        ville:            Ville de résidence (optionnel)
        pays:             Pays de résidence (optionnel, défaut Bénin)
        numero_licence:   Numéro de licence pharmacien (obligatoire si role=pharmacien)
        is_approved:      Compte pharmacien approuvé par un super admin
        notif_push:       Accepte les notifications push (app mobile)
        notif_email:      Accepte les notifications par email
        created_at:       Date de création du compte
        updated_at:       Date de dernière modification
    """

    # ── Rôles ─────────────────────────────────────────────────────────────────
    class Role(models.TextChoices):
        PUBLIC      = "public",      "Utilisateur public"
        PHARMACIEN  = "pharmacien",  "Pharmacien / Gérant"
        SUPER_ADMIN = "super_admin", "Super Administrateur"

    # ── Champs de base ────────────────────────────────────────────────────────
    # email rendu obligatoire et unique pour permettre la connexion par email
    email = models.EmailField(
        unique=True,
        verbose_name="Adresse email",
    )

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.PUBLIC,
        verbose_name="Rôle",
    )
    phone = models.CharField(
        max_length=20,
        blank=True,
        default="",
        verbose_name="Téléphone",
    )

    # ── Avatar ────────────────────────────────────────────────────────────────
    avatar = models.ImageField(
        upload_to=avatar_upload_path,
        null=True,
        blank=True,
        verbose_name="Photo de profil",
    )

    # ── Adresse ───────────────────────────────────────────────────────────────
    ville = models.CharField(
        max_length=100,
        blank=True,
        default="",
        verbose_name="Ville",
    )
    pays = models.CharField(
        max_length=100,
        blank=True,
        default="Bénin",
        verbose_name="Pays",
    )

    # ── Licence pharmacien ────────────────────────────────────────────────────
    # Obligatoire pour role=pharmacien, ignoré pour les autres rôles
    numero_licence = models.CharField(
        max_length=50,
        blank=True,
        default="",
        verbose_name="Numéro de licence",
        help_text="Numéro de licence officielle du pharmacien. Obligatoire pour le rôle pharmacien.",
    )

    # ── Approbation (workflow pharmacien) ─────────────────────────────────────
    is_approved = models.BooleanField(
        default=False,
        verbose_name="Compte approuvé",
        help_text="Doit être activé par un super admin pour les comptes pharmacien.",
    )
    approved_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Date d'approbation",
    )
    approved_by = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="comptes_approuves",
        verbose_name="Approuvé par",
        help_text="Super admin ayant approuvé ce compte.",
    )

    # ── Préférences notifications ─────────────────────────────────────────────
    notif_push = models.BooleanField(
        default=True,
        verbose_name="Notifications push",
        help_text="Recevoir les alertes push sur l'application mobile.",
    )
    notif_email = models.BooleanField(
        default=True,
        verbose_name="Notifications email",
        help_text="Recevoir les alertes par email.",
    )

    # ── Métadonnées ───────────────────────────────────────────────────────────
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # ── Manager custom (connexion email + username) ───────────────────────────
    objects = CustomUserManager()

    # Champ utilisé comme identifiant principal pour l'auth
    # USERNAME_FIELD reste "username" pour la compatibilité Django admin
    # La connexion par email est gérée dans le serializer d'authentification
    USERNAME_FIELD  = "username"
    REQUIRED_FIELDS = ["email"]    # email demandé lors de createsuperuser

    class Meta:
        ordering        = ["-created_at"]
        verbose_name    = "Utilisateur"
        verbose_name_plural = "Utilisateurs"
        indexes = [
            models.Index(fields=["email"],      name="idx_user_email"),
            models.Index(fields=["role"],       name="idx_user_role"),
            models.Index(fields=["is_approved"], name="idx_user_approved"),
        ]

    def __str__(self) -> str:
        return f"{self.username} ({self.get_role_display()})"

    # ── Propriétés utilitaires ────────────────────────────────────────────────
    @property
    def is_pharmacien(self) -> bool:
        """True si l'utilisateur est un pharmacien."""
        return self.role == self.Role.PHARMACIEN

    @property
    def is_super_admin(self) -> bool:
        """True si l'utilisateur est un super administrateur."""
        return self.role == self.Role.SUPER_ADMIN

    @property
    def is_pharmacien_actif(self) -> bool:
        """True si pharmacien ET compte approuvé par un admin."""
        return self.is_pharmacien and self.is_approved

    @property
    def nom_complet(self) -> str:
        """Retourne le nom complet ou le username si non renseigné."""
        full = f"{self.first_name} {self.last_name}".strip()
        return full if full else self.username

    # ── Méthodes métier ───────────────────────────────────────────────────────
    def approuver(self, approuve_par: "CustomUser") -> None:
        """Approuve le compte d'un pharmacien.

        Args:
            approuve_par: Super admin effectuant l'approbation.

        Raises:
            ValueError: Si l'utilisateur n'est pas un pharmacien.
        """
        from django.utils import timezone

        if not self.is_pharmacien:
            raise ValueError("Seuls les comptes pharmacien peuvent être approuvés.")

        self.is_approved = True
        self.approved_at = timezone.now()
        self.approved_by = approuve_par
        self.save(update_fields=["is_approved", "approved_at", "approved_by"])

    def rejeter(self) -> None:
        """Révoque l'approbation d'un pharmacien."""
        self.is_approved = False
        self.approved_at = None
        self.approved_by = None
        self.save(update_fields=["is_approved", "approved_at", "approved_by"])