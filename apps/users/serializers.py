# apps/users/serializers.py
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import CustomUser


# ─────────────────────────────────────────────────────────────────────────────
# LECTURE
# ─────────────────────────────────────────────────────────────────────────────

class CustomUserPublicSerializer(serializers.ModelSerializer):
    """Serializer lecture seule — données publiques minimales.
    Utilisé pour afficher le profil d'un pharmacien dans l'app mobile.
    """

    nom_complet = serializers.ReadOnlyField()

    class Meta:
        model  = CustomUser
        fields = ["id", "username", "nom_complet", "avatar", "ville", "pays"]


class CustomUserSerializer(serializers.ModelSerializer):
    """Serializer lecture — profil complet de l'utilisateur connecté."""

    nom_complet          = serializers.ReadOnlyField()
    is_pharmacien        = serializers.ReadOnlyField()
    is_super_admin       = serializers.ReadOnlyField()
    is_pharmacien_actif  = serializers.ReadOnlyField()

    class Meta:
        model  = CustomUser
        fields = [
            "id", "username", "email", "first_name", "last_name",
            "nom_complet", "role", "phone", "avatar", "ville", "pays",
            "numero_licence", "is_approved", "approved_at",
            "notif_push", "notif_email",
            "is_pharmacien", "is_super_admin", "is_pharmacien_actif",
            "created_at", "updated_at",
        ]
        read_only_fields = [
            "id", "role", "is_approved", "approved_at",
            "created_at", "updated_at",
        ]


# ─────────────────────────────────────────────────────────────────────────────
# INSCRIPTION
# ─────────────────────────────────────────────────────────────────────────────

class InscriptionPublicSerializer(serializers.ModelSerializer):
    """Inscription d'un utilisateur public (app mobile)."""

    password  = serializers.CharField(write_only=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, label="Confirmation mot de passe")

    class Meta:
        model  = CustomUser
        fields = ["username", "email", "password", "password2", "first_name", "last_name", "phone"]

    def validate(self, data):
        if data["password"] != data["password2"]:
            raise serializers.ValidationError({"password2": "Les mots de passe ne correspondent pas."})
        return data

    def create(self, validated_data):
        validated_data.pop("password2")
        password = validated_data.pop("password")
        user = CustomUser(**validated_data, role=CustomUser.Role.PUBLIC)
        user.set_password(password)
        user.save()
        return user


class InscriptionPharmacienSerializer(serializers.ModelSerializer):
    """Inscription d'un pharmacien.

    Après inscription, is_approved=False — le compte est en attente
    d'approbation par un super admin.
    """

    password  = serializers.CharField(write_only=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, label="Confirmation mot de passe")

    class Meta:
        model  = CustomUser
        fields = [
            "username", "email", "password", "password2",
            "first_name", "last_name", "phone",
            "numero_licence", "ville", "pays",
        ]

    def validate(self, data):
        if data["password"] != data["password2"]:
            raise serializers.ValidationError({"password2": "Les mots de passe ne correspondent pas."})
        return data

    def validate_numero_licence(self, value):
        if not value.strip():
            raise serializers.ValidationError("Le numéro de licence est obligatoire pour un pharmacien.")
        return value

    def create(self, validated_data):
        validated_data.pop("password2")
        password = validated_data.pop("password")
        user = CustomUser(
            **validated_data,
            role=CustomUser.Role.PHARMACIEN,
            is_approved=False,
        )
        user.set_password(password)
        user.save()
        return user


# ─────────────────────────────────────────────────────────────────────────────
# MISE À JOUR PROFIL
# ─────────────────────────────────────────────────────────────────────────────

class UpdateProfilSerializer(serializers.ModelSerializer):
    """Mise à jour du profil par l'utilisateur lui-même.
    Le rôle et l'approbation ne sont pas modifiables ici.
    """

    class Meta:
        model  = CustomUser
        fields = [
            "first_name", "last_name", "phone",
            "avatar", "ville", "pays",
            "notif_push", "notif_email",
        ]


class UpdatePasswordSerializer(serializers.Serializer):
    """Changement de mot de passe par l'utilisateur connecté."""

    ancien_password   = serializers.CharField(write_only=True)
    nouveau_password  = serializers.CharField(write_only=True, validators=[validate_password])
    nouveau_password2 = serializers.CharField(write_only=True)

    def validate_ancien_password(self, value):
        user = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError("Mot de passe actuel incorrect.")
        return value

    def validate(self, data):
        if data["nouveau_password"] != data["nouveau_password2"]:
            raise serializers.ValidationError({"nouveau_password2": "Les mots de passe ne correspondent pas."})
        return data

    def save(self):
        user = self.context["request"].user
        user.set_password(self.validated_data["nouveau_password"])
        user.save(update_fields=["password"])
        return user


# ─────────────────────────────────────────────────────────────────────────────
# AUTHENTIFICATION JWT ÉTENDUE
# ─────────────────────────────────────────────────────────────────────────────

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """JWT Login étendu — accepte username OU email.

    Ajoute les infos utilisateur directement dans la réponse du token
    pour éviter un second appel API après login.
    """

    def validate(self, attrs):
        # Essaie d'abord avec le username, puis par email via le manager custom
        data = super().validate(attrs)

        # Vérifie que le pharmacien est approuvé avant de délivrer un token
        user = self.user
        if user.is_pharmacien and not user.is_approved:
            raise serializers.ValidationError(
                "Votre compte est en attente d'approbation par un administrateur."
            )

        # Enrichit la réponse avec les données utilisateur
        data["user"] = {
            "id":           user.id,
            "username":     user.username,
            "email":        user.email,
            "nom_complet":  user.nom_complet,
            "role":         user.role,
            "is_approved":  user.is_approved,
            "avatar":       user.avatar.url if user.avatar else None,
        }
        return data


# ─────────────────────────────────────────────────────────────────────────────
# ADMIN — GESTION DES COMPTES
# ─────────────────────────────────────────────────────────────────────────────

class AdminUserListSerializer(serializers.ModelSerializer):
    """Liste des utilisateurs pour le dashboard super admin."""

    nom_complet = serializers.ReadOnlyField()

    class Meta:
        model  = CustomUser
        fields = [
            "id", "username", "email", "nom_complet", "role",
            "is_approved", "is_active", "numero_licence",
            "ville", "pays", "created_at",
        ]
        read_only_fields = fields


class AdminApprobationSerializer(serializers.Serializer):
    """Approbation ou rejet d'un compte pharmacien par le super admin."""

    action = serializers.ChoiceField(choices=["approuver", "rejeter"])

    def validate(self, data):
        user = self.context["user"]
        if not user.is_pharmacien:
            raise serializers.ValidationError("Seuls les comptes pharmacien peuvent être approuvés.")
        return data

    def save(self):
        user      = self.context["user"]
        admin     = self.context["request"].user
        action    = self.validated_data["action"]

        if action == "approuver":
            user.approuver(approuve_par=admin)
        else:
            user.rejeter()
        return user