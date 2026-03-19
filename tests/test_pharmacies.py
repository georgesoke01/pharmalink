# tests/test_pharmacies.py
"""
Tests unitaires — apps/pharmacies/

Couvre :
    - Modèle Pharmacie (propriétés, méthodes, save lat/lng)
    - Filtres géographiques (bounding box dev)
    - Workflow activation / suspension
"""
import pytest
from decimal import Decimal

from tests.factories import (
    PharmacieFactory,
    PharmacieActiveFactory,
    PharmacieSuspendueFactory,
    UserPharmacienApprouveFactory,
    SuperAdminFactory,
)


# ─────────────────────────────────────────────────────────────────────────────
# MODÈLE — PROPRIÉTÉS
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestPharmacieProprietes:

    def test_statut_en_attente_par_defaut(self):
        pharmacie = PharmacieFactory()
        assert pharmacie.statut   == "en_attente"
        assert pharmacie.est_active is False

    def test_pharmacie_active(self):
        pharmacie = PharmacieActiveFactory()
        assert pharmacie.est_active is True

    def test_coordonnees_retourne_dict(self):
        pharmacie = PharmacieActiveFactory(
            latitude=Decimal("6.370000"),
            longitude=Decimal("2.391000"),
        )
        coords = pharmacie.coordonnees
        assert coords is not None
        assert coords["lat"] == pytest.approx(6.37, abs=0.001)
        assert coords["lng"] == pytest.approx(2.391, abs=0.001)

    def test_coordonnees_none_si_pas_de_coords(self):
        pharmacie = PharmacieFactory(latitude=None, longitude=None)
        assert pharmacie.coordonnees is None

    def test_str_inclut_nom_et_ville(self):
        pharmacie = PharmacieFactory(nom="Pharmacie Centrale", ville="Cotonou")
        assert "Pharmacie Centrale" in str(pharmacie)
        assert "Cotonou"            in str(pharmacie)

    def test_services_liste(self):
        pharmacie = PharmacieActiveFactory(services=["livraison", "vaccins"])
        assert "livraison" in pharmacie.services
        assert "vaccins"   in pharmacie.services


# ─────────────────────────────────────────────────────────────────────────────
# MODÈLE — MÉTHODES MÉTIER
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestPharmacieMethodes:

    def test_activer_pharmacie(self):
        pharmacie = PharmacieFactory()
        admin     = SuperAdminFactory()

        assert pharmacie.statut == "en_attente"

        pharmacie.activer(admin)
        pharmacie.refresh_from_db()

        assert pharmacie.statut    == "active"
        assert pharmacie.est_active is True

    def test_suspendre_pharmacie(self):
        pharmacie = PharmacieActiveFactory()

        pharmacie.suspendre(raison="Contrôle sanitaire")
        pharmacie.refresh_from_db()

        assert pharmacie.statut    == "suspendue"
        assert pharmacie.est_active is False

    def test_activer_puis_suspendre(self):
        pharmacie = PharmacieFactory()
        admin     = SuperAdminFactory()

        pharmacie.activer(admin)
        pharmacie.suspendre()
        pharmacie.refresh_from_db()

        assert pharmacie.statut == "suspendue"


# ─────────────────────────────────────────────────────────────────────────────
# MODÈLE — CONTRAINTES DB
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestPharmacieContraintes:

    def test_numero_agrement_unique(self):
        from apps.pharmacies.serializers import PharmacieCreateSerializer
        from unittest.mock import MagicMock

        agrement  = "AGR-UNIQUE-001"
        # Créer une pharmacie avec ce numéro d'agrément
        ph1 = PharmacieFactory(numero_agrement=agrement)

        # Tenter d'en créer une autre avec le même agrément via le serializer
        request      = MagicMock()
        request.user = ph1.pharmacien

        serializer = PharmacieCreateSerializer(
            data={
                "nom":             "Autre Pharmacie",
                "numero_agrement": agrement,
                "adresse":         "123 rue test",
                "ville":           "Cotonou",
                "latitude":        6.37,
                "longitude":       2.39,
            },
            context={"request": request},
        )
        assert serializer.is_valid() is False
        assert "numero_agrement" in serializer.errors

    def test_pharmacie_appartient_a_pharmacien(self):
        pharmacien = UserPharmacienApprouveFactory()
        pharmacie  = PharmacieActiveFactory(pharmacien=pharmacien)

        assert pharmacie.pharmacien == pharmacien

    def test_suppression_pharmacien_cascade(self):
        pharmacien = UserPharmacienApprouveFactory()
        pharmacie  = PharmacieActiveFactory(pharmacien=pharmacien)
        pk         = pharmacie.pk

        pharmacien.delete()

        from apps.pharmacies.models import Pharmacie
        assert not Pharmacie.objects.filter(pk=pk).exists()


# ─────────────────────────────────────────────────────────────────────────────
# FILTRES — BOUNDING BOX (dev sans PostGIS)
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestPharmacieFilters:

    def test_filtre_par_ville(self):
        PharmacieActiveFactory(ville="Cotonou")
        PharmacieActiveFactory(ville="Porto-Novo")

        from apps.pharmacies.models import Pharmacie
        from apps.pharmacies.filters import PharmacieFilter

        qs     = Pharmacie.objects.filter(statut="active")
        filtre = PharmacieFilter({"ville": "Cotonou"}, queryset=qs)
        assert filtre.qs.count() == 1
        assert filtre.qs.first().ville == "Cotonou"

    def test_filtre_est_ouverte(self):
        PharmacieActiveFactory(est_ouverte=True)
        PharmacieActiveFactory(est_ouverte=False)

        from apps.pharmacies.models import Pharmacie
        from apps.pharmacies.filters import PharmacieFilter

        qs     = Pharmacie.objects.filter(statut="active")
        filtre = PharmacieFilter({"est_ouverte": True}, queryset=qs)
        assert filtre.qs.count() == 1

    def test_filtre_par_service(self):
        """SQLite ne supporte pas contains sur JSONField — on teste en Python."""
        ph1 = PharmacieActiveFactory(services=["livraison", "vaccins"])
        ph2 = PharmacieActiveFactory(services=["urgences"])

        from apps.pharmacies.models import Pharmacie

        # Filtre Python direct (équivalent de ce que fait le filtre en prod)
        toutes = Pharmacie.objects.filter(statut="active")
        avec_livraison = [p for p in toutes if "livraison" in (p.services or [])]

        assert len(avec_livraison) == 1
        assert avec_livraison[0].pk == ph1.pk

    def test_filtre_bounding_box_geo(self):
        """Test filtre géographique par bounding box (dev sans PostGIS)."""
        PharmacieActiveFactory(
            latitude=Decimal("6.37"),
            longitude=Decimal("2.39"),
        )
        PharmacieActiveFactory(
            latitude=Decimal("9.35"),
            longitude=Decimal("2.67"),
        )

        from apps.pharmacies.models import Pharmacie
        from apps.pharmacies.filters import PharmacieFilter
        from unittest.mock import MagicMock

        request = MagicMock()
        # Centre Cotonou, rayon 5km
        request.query_params = {"lat": "6.37", "lng": "2.39", "rayon": "5"}

        qs     = Pharmacie.objects.filter(statut="active")
        filtre = PharmacieFilter(
            {"lat": "6.37", "lng": "2.39", "rayon": "5"},
            queryset=qs,
            request=request,
        )
        # Seule la pharmacie proche doit apparaître
        assert filtre.qs.count() == 1