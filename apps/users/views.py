# apps/users/views.py
from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView

from .models import CustomUser
from .serializers import (
    CustomUserSerializer,
    CustomUserPublicSerializer,
    InscriptionPublicSerializer,
    InscriptionPharmacienSerializer,
    UpdateProfilSerializer,
    UpdatePasswordSerializer,
    CustomTokenObtainPairSerializer,
    AdminUserListSerializer,
    AdminApprobationSerializer,
)
from .permissions import IsSuperAdmin, IsSelfOrSuperAdmin


# ─────────────────────────────────────────────────────────────────────────────
# AUTHENTIFICATION
# ─────────────────────────────────────────────────────────────────────────────

class CustomTokenObtainPairView(TokenObtainPairView):
    """POST /api/v1/auth/token/
    Login JWT — accepte username OU email + password.
    Retourne access, refresh + données utilisateur.
    """
    serializer_class = CustomTokenObtainPairSerializer


# ─────────────────────────────────────────────────────────────────────────────
# INSCRIPTION
# ─────────────────────────────────────────────────────────────────────────────

class InscriptionPublicView(generics.CreateAPIView):
    """POST /api/v1/users/inscription/public/
    Inscription d'un utilisateur public (app mobile).
    Accessible sans authentification.
    """
    serializer_class   = InscriptionPublicSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(
            {
                "message": "Compte créé avec succès.",
                "user":    CustomUserSerializer(user).data,
            },
            status=status.HTTP_201_CREATED,
        )


class InscriptionPharmacienView(generics.CreateAPIView):
    """POST /api/v1/users/inscription/pharmacien/
    Inscription d'un pharmacien — compte en attente d'approbation.
    Accessible sans authentification.
    """
    serializer_class   = InscriptionPharmacienSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(
            {
                "message": (
                    "Compte pharmacien créé avec succès. "
                    "Votre compte est en attente d'approbation par un administrateur."
                ),
                "user": CustomUserSerializer(user).data,
            },
            status=status.HTTP_201_CREATED,
        )


# ─────────────────────────────────────────────────────────────────────────────
# PROFIL UTILISATEUR CONNECTÉ
# ─────────────────────────────────────────────────────────────────────────────

class MonProfilView(generics.RetrieveUpdateAPIView):
    """GET  /api/v1/users/moi/   → récupère son propre profil
    PATCH /api/v1/users/moi/   → met à jour son propre profil
    """
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method in ["PUT", "PATCH"]:
            return UpdateProfilSerializer
        return CustomUserSerializer

    def get_object(self):
        return self.request.user


class UpdatePasswordView(APIView):
    """POST /api/v1/users/moi/password/
    Changement de mot de passe par l'utilisateur connecté.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = UpdatePasswordSerializer(
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {"message": "Mot de passe modifié avec succès."},
            status=status.HTTP_200_OK,
        )


# ─────────────────────────────────────────────────────────────────────────────
# ADMIN — GESTION DES UTILISATEURS
# ─────────────────────────────────────────────────────────────────────────────

class AdminUserListView(generics.ListAPIView):
    """GET /api/v1/users/admin/
    Liste tous les utilisateurs — super admin uniquement.
    Supporte les filtres : ?role=pharmacien&is_approved=false
    """
    serializer_class   = AdminUserListSerializer
    permission_classes = [IsSuperAdmin]

    def get_queryset(self):
        qs = CustomUser.objects.all()

        role       = self.request.query_params.get("role")
        is_approved = self.request.query_params.get("is_approved")
        search     = self.request.query_params.get("search")

        if role:
            qs = qs.filter(role=role)
        if is_approved is not None:
            qs = qs.filter(is_approved=is_approved.lower() == "true")
        if search:
            qs = qs.filter(
                username__icontains=search
            ) | qs.filter(
                email__icontains=search
            ) | qs.filter(
                first_name__icontains=search
            ) | qs.filter(
                last_name__icontains=search
            )
        return qs


class AdminUserDetailView(generics.RetrieveUpdateDestroyAPIView):
    """GET    /api/v1/users/admin/<id>/   → détail d'un utilisateur
    PATCH  /api/v1/users/admin/<id>/   → modifier un utilisateur
    DELETE /api/v1/users/admin/<id>/   → désactiver un utilisateur
    Super admin uniquement.
    """
    serializer_class   = AdminUserListSerializer
    permission_classes = [IsSuperAdmin]
    queryset           = CustomUser.objects.all()

    def destroy(self, request, *args, **kwargs):
        """Désactive le compte au lieu de le supprimer définitivement."""
        user = self.get_object()
        user.is_active = False
        user.save(update_fields=["is_active"])
        return Response(
            {"message": f"Compte de {user.username} désactivé."},
            status=status.HTTP_200_OK,
        )


class AdminApprobationView(APIView):
    """POST /api/v1/users/admin/<id>/approbation/
    Approuver ou rejeter un compte pharmacien.
    Body : { "action": "approuver" | "rejeter" }
    Super admin uniquement.
    """
    permission_classes = [IsSuperAdmin]

    def post(self, request, pk):
        try:
            user = CustomUser.objects.get(pk=pk)
        except CustomUser.DoesNotExist:
            return Response(
                {"error": "Utilisateur introuvable."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = AdminApprobationSerializer(
            data=request.data,
            context={"user": user, "request": request},
        )
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        action  = serializer.validated_data["action"]
        message = (
            f"Compte de {user.username} approuvé avec succès."
            if action == "approuver"
            else f"Compte de {user.username} rejeté."
        )
        return Response(
            {"message": message, "user": AdminUserListSerializer(user).data},
            status=status.HTTP_200_OK,
        )


class AdminPharmacienEnAttenteView(generics.ListAPIView):
    """GET /api/v1/users/admin/en-attente/
    Liste les pharmaciens en attente d'approbation.
    Raccourci pratique pour le dashboard admin.
    """
    serializer_class   = AdminUserListSerializer
    permission_classes = [IsSuperAdmin]

    def get_queryset(self):
        return CustomUser.objects.filter(
            role=CustomUser.Role.PHARMACIEN,
            is_approved=False,
            is_active=True,
        )