# apps/users/permissions.py
from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsPharmacien(BasePermission):
    """Accès réservé aux pharmaciens dont le compte est approuvé."""

    message = "Votre compte pharmacien est en attente d'approbation."

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.is_pharmacien
            and request.user.is_approved
        )


class IsSuperAdmin(BasePermission):
    """Accès réservé aux super administrateurs."""

    message = "Accès réservé aux super administrateurs."

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.is_super_admin
        )


class IsOwnerOrSuperAdmin(BasePermission):
    """Lecture/écriture sur ses propres ressources uniquement.
    Super admin peut tout voir et modifier.
    """

    message = "Vous ne pouvez accéder qu'à vos propres ressources."

    def has_object_permission(self, request, view, obj):
        if request.user.is_super_admin:
            return True
        # obj peut être un CustomUser ou un objet avec un champ .user ou .pharmacien
        if hasattr(obj, "pharmacien"):
            return obj.pharmacien == request.user
        return obj == request.user


class IsSelfOrSuperAdmin(BasePermission):
    """Un utilisateur peut modifier uniquement son propre profil.
    Super admin peut modifier n'importe quel profil.
    """

    message = "Vous ne pouvez modifier que votre propre profil."

    def has_object_permission(self, request, view, obj):
        if request.user.is_super_admin:
            return True
        return obj == request.user


class IsPharmacienOrSuperAdmin(BasePermission):
    """Pharmacien approuvé OU super admin."""

    message = "Accès réservé aux pharmaciens approuvés ou aux administrateurs."

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        return request.user.is_super_admin or (
            request.user.is_pharmacien and request.user.is_approved
        )


class ReadOnly(BasePermission):
    """Accès en lecture seule (GET, HEAD, OPTIONS).
    Utilisé pour les endpoints publics de l'app mobile.
    """

    def has_permission(self, request, view):
        return request.method in SAFE_METHODS