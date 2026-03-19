# tests/conftest.py
"""
Configuration globale pytest — fixtures réutilisables dans tous les tests.

Usage :
    pytest                        → tous les tests
    pytest tests/test_users.py    → app users uniquement
    pytest -k "test_inscription"  → tests filtrés par nom
    pytest -v --tb=short          → verbose avec traceback court
"""
import pytest
from rest_framework.test import APIClient

from tests.factories import (
    UserPublicFactory,
    UserPharmacienFactory,
    UserPharmacienApprouveFactory,
    SuperAdminFactory,
    PharmacieFactory,
    PharmacieActiveFactory,
    ProduitFactory,
    StockFactory,
    PrixFactory,
    HoraireSemaineFactory,
    HoraireExceptionnelFactory,
    PeriodeGardeFactory,
    ConnexionLGOFactory,
)


# ─────────────────────────────────────────────────────────────────────────────
# CLIENTS API
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture
def api_client():
    """Client API non authentifié."""
    return APIClient()


@pytest.fixture
def client_public(user_public):
    """Client API authentifié en tant qu'utilisateur public."""
    client = APIClient()
    client.force_authenticate(user=user_public)
    return client


@pytest.fixture
def client_pharmacien(pharmacien_approuve):
    """Client API authentifié en tant que pharmacien approuvé."""
    client = APIClient()
    client.force_authenticate(user=pharmacien_approuve)
    return client


@pytest.fixture
def client_admin(super_admin):
    """Client API authentifié en tant que super admin."""
    client = APIClient()
    client.force_authenticate(user=super_admin)
    return client


# ─────────────────────────────────────────────────────────────────────────────
# UTILISATEURS
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture
def user_public(db):
    return UserPublicFactory()


@pytest.fixture
def pharmacien(db):
    """Pharmacien non approuvé."""
    return UserPharmacienFactory()


@pytest.fixture
def pharmacien_approuve(db):
    """Pharmacien approuvé — peut accéder aux endpoints protégés."""
    return UserPharmacienApprouveFactory()


@pytest.fixture
def super_admin(db):
    return SuperAdminFactory()


# ─────────────────────────────────────────────────────────────────────────────
# PHARMACIES
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture
def pharmacie(db, pharmacien_approuve):
    return PharmacieFactory(pharmacien=pharmacien_approuve)


@pytest.fixture
def pharmacie_active(db, pharmacien_approuve):
    return PharmacieActiveFactory(pharmacien=pharmacien_approuve)


# ─────────────────────────────────────────────────────────────────────────────
# PRODUITS / STOCKS / PRIX
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture
def produit(db):
    return ProduitFactory()


@pytest.fixture
def stock(db, pharmacie_active, produit):
    return StockFactory(pharmacie=pharmacie_active, produit=produit)


@pytest.fixture
def prix(db, pharmacie_active, produit):
    return PrixFactory(pharmacie=pharmacie_active, produit=produit)


# ─────────────────────────────────────────────────────────────────────────────
# HORAIRES
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture
def horaire_semaine(db, pharmacie_active):
    return HoraireSemaineFactory(pharmacie=pharmacie_active)


@pytest.fixture
def horaire_exceptionnel(db, pharmacie_active):
    return HoraireExceptionnelFactory(pharmacie=pharmacie_active)


# ─────────────────────────────────────────────────────────────────────────────
# GARDES
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture
def garde_planifiee(db, pharmacie_active):
    return PeriodeGardeFactory(pharmacie=pharmacie_active)


# ─────────────────────────────────────────────────────────────────────────────
# CONNECTEURS LGO
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture
def connexion_lgo(db, pharmacie_active):
    return ConnexionLGOFactory(pharmacie=pharmacie_active)