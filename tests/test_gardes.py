# tests/test_gardes.py
"""
Tests unitaires — apps/gardes/

Couvre :
    - Modèle PeriodeGarde (propriétés, machine à états)
    - Méthodes activer(), terminer(), annuler()
    - Mise à jour de est_de_garde sur la pharmacie
    - Validation chevauchement dans le serializer
    - Tâche Celery mise_a_jour_statut_gardes()
"""
import pytest
from datetime import timedelta
from django.utils import timezone
from unittest.mock import patch, MagicMock

from tests.factories import (
    PharmacieActiveFactory,
    PeriodeGardeFactory,
    PeriodeGardeEnCoursFactory,
    PeriodeGardeTermineeFactory,
)


# ─────────────────────────────────────────────────────────────────────────────
# MODÈLE — PROPRIÉTÉS
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestPeriodeGardeProprietes:

    def test_garde_planifiee_pas_encore_active(self):
        garde = PeriodeGardeFactory()  # début dans 2h
        assert garde.est_active_maintenant is False
        assert garde.est_a_venir          is True
        assert garde.est_passee           is False

    def test_garde_en_cours(self):
        garde = PeriodeGardeEnCoursFactory()  # commencée il y a 2h
        assert garde.est_active_maintenant is True
        assert garde.est_a_venir          is False
        assert garde.est_passee           is False

    def test_garde_terminee(self):
        garde = PeriodeGardeTermineeFactory()
        assert garde.est_active_maintenant is False
        assert garde.est_passee           is True

    def test_telephone_effectif_utilise_pharmacie_si_vide(self):
        pharmacie = PharmacieActiveFactory(telephone="+22997000001")
        garde     = PeriodeGardeFactory(pharmacie=pharmacie, telephone_garde="")
        assert garde.telephone_effectif == "+22997000001"

    def test_telephone_effectif_priorite_garde(self):
        pharmacie = PharmacieActiveFactory(telephone="+22997000001")
        garde     = PeriodeGardeFactory(pharmacie=pharmacie, telephone_garde="+22997999999")
        assert garde.telephone_effectif == "+22997999999"

    def test_str_inclut_pharmacie_et_statut(self):
        garde = PeriodeGardeFactory()
        assert garde.pharmacie.nom       in str(garde)
        assert garde.get_statut_display() in str(garde)


# ─────────────────────────────────────────────────────────────────────────────
# MODÈLE — MACHINE À ÉTATS
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestPeriodeGardeMachineEtats:

    def test_activer_garde(self):
        pharmacie = PharmacieActiveFactory()
        garde     = PeriodeGardeFactory(pharmacie=pharmacie)

        assert garde.statut             == "planifiee"
        assert pharmacie.est_de_garde   is False

        garde.activer()
        garde.refresh_from_db()
        pharmacie.refresh_from_db()

        assert garde.statut           == "en_cours"
        assert pharmacie.est_de_garde is True

    def test_terminer_garde(self):
        pharmacie = PharmacieActiveFactory()
        garde     = PeriodeGardeEnCoursFactory(pharmacie=pharmacie)
        pharmacie.est_de_garde = True
        pharmacie.save()

        garde.terminer()
        garde.refresh_from_db()
        pharmacie.refresh_from_db()

        assert garde.statut           == "terminee"
        assert pharmacie.est_de_garde is False

    def test_terminer_garde_pas_desactiver_si_autre_garde_active(self):
        """Si une autre garde est active en parallèle, est_de_garde reste True."""
        pharmacie = PharmacieActiveFactory()

        garde1 = PeriodeGardeEnCoursFactory(pharmacie=pharmacie)
        garde2 = PeriodeGardeEnCoursFactory(pharmacie=pharmacie)
        pharmacie.est_de_garde = True
        pharmacie.save()

        garde1.terminer()
        pharmacie.refresh_from_db()

        # garde2 est encore active → est_de_garde doit rester True
        assert pharmacie.est_de_garde is True

    def test_annuler_garde_planifiee(self):
        pharmacie = PharmacieActiveFactory()
        garde     = PeriodeGardeFactory(pharmacie=pharmacie)

        garde.annuler()
        garde.refresh_from_db()

        assert garde.statut == "annulee"

    def test_annuler_garde_en_cours_desactive_pharmacie(self):
        pharmacie = PharmacieActiveFactory()
        garde     = PeriodeGardeEnCoursFactory(pharmacie=pharmacie)
        pharmacie.est_de_garde = True
        pharmacie.save()

        garde.annuler()
        pharmacie.refresh_from_db()

        assert pharmacie.est_de_garde is False


# ─────────────────────────────────────────────────────────────────────────────
# SERIALIZER — VALIDATION CHEVAUCHEMENT
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestGardeSerializerValidation:

    def test_creation_garde_valide(self):
        pharmacie = PharmacieActiveFactory()
        now       = timezone.now()

        from apps.gardes.serializers import PeriodeGardeCreateSerializer

        data = {
            "date_debut":     (now + timedelta(hours=2)).isoformat(),
            "date_fin":       (now + timedelta(hours=14)).isoformat(),
            "telephone_garde": "+22997000001",
            "zone_ville":     "Cotonou",
        }
        serializer = PeriodeGardeCreateSerializer(
            data=data,
            context={"pharmacie": pharmacie},
        )
        assert serializer.is_valid(), serializer.errors

    def test_date_fin_avant_debut_invalide(self):
        pharmacie = PharmacieActiveFactory()
        now       = timezone.now()

        from apps.gardes.serializers import PeriodeGardeCreateSerializer

        data = {
            "date_debut": (now + timedelta(hours=10)).isoformat(),
            "date_fin":   (now + timedelta(hours=2)).isoformat(),
        }
        serializer = PeriodeGardeCreateSerializer(
            data=data, context={"pharmacie": pharmacie}
        )
        assert serializer.is_valid() is False
        assert "date_fin" in serializer.errors

    def test_date_debut_dans_passe_invalide(self):
        pharmacie = PharmacieActiveFactory()
        now       = timezone.now()

        from apps.gardes.serializers import PeriodeGardeCreateSerializer

        data = {
            "date_debut": (now - timedelta(hours=2)).isoformat(),
            "date_fin":   (now + timedelta(hours=6)).isoformat(),
        }
        serializer = PeriodeGardeCreateSerializer(
            data=data, context={"pharmacie": pharmacie}
        )
        assert serializer.is_valid() is False
        assert "date_debut" in serializer.errors

    def test_chevauchement_avec_garde_existante(self):
        pharmacie = PharmacieActiveFactory()
        now       = timezone.now()

        # Garde existante de J+2h à J+14h
        PeriodeGardeFactory(
            pharmacie=pharmacie,
            date_debut=now + timedelta(hours=2),
            date_fin=now + timedelta(hours=14),
            statut="planifiee",
        )

        from apps.gardes.serializers import PeriodeGardeCreateSerializer

        # Nouvelle garde qui chevauche
        data = {
            "date_debut": (now + timedelta(hours=5)).isoformat(),
            "date_fin":   (now + timedelta(hours=20)).isoformat(),
        }
        serializer = PeriodeGardeCreateSerializer(
            data=data, context={"pharmacie": pharmacie}
        )
        assert serializer.is_valid() is False
        assert any("chevauche" in str(e) for e in serializer.errors.get("non_field_errors", []))


# ─────────────────────────────────────────────────────────────────────────────
# TÂCHE CELERY — mise_a_jour_statut_gardes
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestCeleryMiseAJourGardes:

    def test_active_gardes_dont_debut_est_passe(self):
        from apps.connecteurs_lgo.tasks import mise_a_jour_statut_gardes

        pharmacie = PharmacieActiveFactory()
        garde     = PeriodeGardeFactory(
            pharmacie=pharmacie,
            date_debut=timezone.now() - timedelta(minutes=5),
            date_fin=timezone.now() + timedelta(hours=8),
            statut="planifiee",
        )

        result = mise_a_jour_statut_gardes()

        garde.refresh_from_db()
        assert garde.statut       == "en_cours"
        assert result["activees"] == 1

    def test_termine_gardes_dont_fin_est_passee(self):
        from apps.connecteurs_lgo.tasks import mise_a_jour_statut_gardes

        pharmacie = PharmacieActiveFactory(est_de_garde=True)
        pharmacie.est_de_garde = True
        pharmacie.save()

        garde = PeriodeGardeEnCoursFactory(
            pharmacie=pharmacie,
            date_debut=timezone.now() - timedelta(hours=8),
            date_fin=timezone.now() - timedelta(minutes=5),
            statut="en_cours",
        )

        result = mise_a_jour_statut_gardes()

        garde.refresh_from_db()
        pharmacie.refresh_from_db()

        assert garde.statut        == "terminee"
        assert result["terminees"] == 1
        assert pharmacie.est_de_garde is False

    def test_ne_touche_pas_les_gardes_terminees(self):
        from apps.connecteurs_lgo.tasks import mise_a_jour_statut_gardes

        garde = PeriodeGardeTermineeFactory()

        mise_a_jour_statut_gardes()

        garde.refresh_from_db()
        assert garde.statut == "terminee"