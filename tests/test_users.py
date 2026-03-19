# tests/test_users.py
"""
Tests unitaires — apps/users/

Couvre :
    - Modèle CustomUser (propriétés, méthodes métier)
    - Manager (connexion email + username)
    - Workflow approbation pharmacien
"""
import pytest
from django.utils import timezone

from tests.factories import (
    UserPublicFactory,
    UserPharmacienFactory,
    UserPharmacienApprouveFactory,
    SuperAdminFactory,
)


# ─────────────────────────────────────────────────────────────────────────────
# MODÈLE — PROPRIÉTÉS
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestCustomUserProprietes:

    def test_role_public_par_defaut(self):
        user = UserPublicFactory()
        assert user.role == "public"
        assert user.is_pharmacien is False
        assert user.is_super_admin is False

    def test_role_pharmacien(self):
        user = UserPharmacienFactory()
        assert user.is_pharmacien is True
        assert user.is_super_admin is False

    def test_role_super_admin(self):
        admin = SuperAdminFactory()
        assert admin.is_super_admin is True
        assert admin.is_pharmacien is False

    def test_pharmacien_non_approuve_nest_pas_actif(self):
        user = UserPharmacienFactory()
        assert user.is_pharmacien_actif is False

    def test_pharmacien_approuve_est_actif(self):
        user = UserPharmacienApprouveFactory()
        assert user.is_pharmacien_actif is True

    def test_nom_complet_avec_prenom_nom(self):
        user = UserPublicFactory(first_name="Jean", last_name="Dupont")
        assert user.nom_complet == "Jean Dupont"

    def test_nom_complet_fallback_username(self):
        user = UserPublicFactory(first_name="", last_name="")
        assert user.nom_complet == user.username

    def test_str_representation(self):
        user = UserPublicFactory(username="testuser")
        assert "testuser" in str(user)
        assert "Utilisateur public" in str(user)


# ─────────────────────────────────────────────────────────────────────────────
# MODÈLE — WORKFLOW APPROBATION
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestWorkflowApprobation:

    def test_approuver_pharmacien(self):
        pharmacien = UserPharmacienFactory()
        admin      = SuperAdminFactory()

        assert pharmacien.is_approved is False

        pharmacien.approuver(approuve_par=admin)

        pharmacien.refresh_from_db()
        assert pharmacien.is_approved is True
        assert pharmacien.approved_by  == admin
        assert pharmacien.approved_at  is not None

    def test_approuver_fixe_horodatage(self):
        pharmacien = UserPharmacienFactory()
        admin      = SuperAdminFactory()
        avant      = timezone.now()

        pharmacien.approuver(approuve_par=admin)

        pharmacien.refresh_from_db()
        assert pharmacien.approved_at >= avant

    def test_approuver_user_public_leve_erreur(self):
        user  = UserPublicFactory()
        admin = SuperAdminFactory()

        with pytest.raises(ValueError, match="pharmacien"):
            user.approuver(approuve_par=admin)

    def test_rejeter_pharmacien(self):
        pharmacien = UserPharmacienApprouveFactory()
        assert pharmacien.is_approved is True

        pharmacien.rejeter()

        pharmacien.refresh_from_db()
        assert pharmacien.is_approved   is False
        assert pharmacien.approved_at   is None
        assert pharmacien.approved_by   is None

    def test_rejeter_puis_reapprouver(self):
        pharmacien = UserPharmacienFactory()
        admin      = SuperAdminFactory()

        pharmacien.approuver(approuve_par=admin)
        pharmacien.rejeter()
        pharmacien.approuver(approuve_par=admin)

        pharmacien.refresh_from_db()
        assert pharmacien.is_approved is True


# ─────────────────────────────────────────────────────────────────────────────
# MANAGER — CONNEXION EMAIL + USERNAME
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestCustomUserManager:

    def test_connexion_par_username(self):
        user = UserPublicFactory(username="monuser")
        from apps.users.models import CustomUser

        trouve = CustomUser.objects.get_by_natural_key("monuser")
        assert trouve == user

    def test_connexion_par_email(self):
        user = UserPublicFactory(email="jean@test.com")
        from apps.users.models import CustomUser

        trouve = CustomUser.objects.get_by_natural_key("jean@test.com")
        assert trouve == user

    def test_connexion_insensible_casse_username(self):
        user = UserPublicFactory(username="MonUser")
        from apps.users.models import CustomUser

        trouve = CustomUser.objects.get_by_natural_key("monuser")
        assert trouve == user

    def test_connexion_insensible_casse_email(self):
        user = UserPublicFactory(email="Jean@Test.Com")
        from apps.users.models import CustomUser

        trouve = CustomUser.objects.get_by_natural_key("jean@test.com")
        assert trouve == user

    def test_createsuperuser_role_admin(self):
        from apps.users.models import CustomUser

        admin = CustomUser.objects.create_superuser(
            username="superadmin",
            email="admin@pharmalink.bj",
            password="strongpass123!",
        )
        assert admin.role        == "super_admin"
        assert admin.is_approved is True
        assert admin.is_staff    is True


# ─────────────────────────────────────────────────────────────────────────────
# CONTRAINTES DB
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestContraintesDB:

    def test_email_unique(self):
        from django.db import IntegrityError

        UserPublicFactory(email="doublon@test.com")
        with pytest.raises(IntegrityError):
            UserPublicFactory(email="doublon@test.com")

    def test_username_unique(self):
        from django.db import IntegrityError
        from apps.users.models import CustomUser

        UserPublicFactory(username="doublon")
        with pytest.raises(IntegrityError):
            CustomUser.objects.create_user(
                username="doublon",
                email="autre@test.com",
                password="pass",
            )