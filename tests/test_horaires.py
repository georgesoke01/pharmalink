# tests/test_horaires.py
"""
Tests unitaires — apps/horaires/

Couvre :
    - est_ouvert_a() sur HoraireSemaine
    - Double plage horaire (pause midi)
    - est_ouverte_maintenant() avec priorité exceptionnel > hebdomadaire
    - HoraireSemaineBulkSerializer (7 jours d'un coup)
    - Validations croisées (ouverture < fermeture, pauses cohérentes)
"""
import pytest
import datetime
from unittest.mock import patch
from django.utils import timezone

from tests.factories import (
    PharmacieActiveFactory,
    HoraireSemaineFactory,
    HoraireFermeFactory,
    HoraireAvecPauseFactory,
    HoraireExceptionnelFactory,
    HoraireExceptionnelOuvertFactory,
)


# ─────────────────────────────────────────────────────────────────────────────
# MODÈLE HORAIRE SEMAINE — est_ouvert_a()
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestHoraireSemaineEstOuvert:

    def test_ouvert_dans_plage(self):
        horaire = HoraireSemaineFactory(
            heure_ouverture=datetime.time(8, 0),
            heure_fermeture=datetime.time(20, 0),
        )
        assert horaire.est_ouvert_a(datetime.time(10, 0)) is True
        assert horaire.est_ouvert_a(datetime.time(19, 59)) is True

    def test_ferme_avant_ouverture(self):
        horaire = HoraireSemaineFactory(
            heure_ouverture=datetime.time(8, 0),
            heure_fermeture=datetime.time(20, 0),
        )
        assert horaire.est_ouvert_a(datetime.time(7, 59)) is False

    def test_ferme_apres_fermeture(self):
        horaire = HoraireSemaineFactory(
            heure_ouverture=datetime.time(8, 0),
            heure_fermeture=datetime.time(20, 0),
        )
        assert horaire.est_ouvert_a(datetime.time(20, 1)) is False

    def test_ferme_toute_la_journee(self):
        horaire = HoraireFermeFactory()
        assert horaire.est_ouvert_a(datetime.time(10, 0)) is False

    def test_ouvert_sans_heures_defini(self):
        horaire = HoraireSemaineFactory(
            heure_ouverture=None,
            heure_fermeture=None,
            est_ferme=False,
        )
        assert horaire.est_ouvert_a(datetime.time(10, 0)) is False


# ─────────────────────────────────────────────────────────────────────────────
# MODÈLE HORAIRE — DOUBLE PLAGE (PAUSE MIDI)
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestDoublePlagePauseMidi:

    def test_ouvert_matin_avant_pause(self):
        horaire = HoraireAvecPauseFactory(
            heure_ouverture=datetime.time(8, 0),
            heure_fermeture=datetime.time(20, 0),
            pause_debut=datetime.time(12, 30),
            pause_fin=datetime.time(14, 30),
        )
        assert horaire.est_ouvert_a(datetime.time(10, 0)) is True

    def test_ferme_pendant_pause(self):
        horaire = HoraireAvecPauseFactory(
            heure_ouverture=datetime.time(8, 0),
            heure_fermeture=datetime.time(20, 0),
            pause_debut=datetime.time(12, 30),
            pause_fin=datetime.time(14, 30),
        )
        assert horaire.est_ouvert_a(datetime.time(13, 0)) is False
        assert horaire.est_ouvert_a(datetime.time(12, 30)) is False

    def test_ouvert_apres_midi_apres_pause(self):
        horaire = HoraireAvecPauseFactory(
            heure_ouverture=datetime.time(8, 0),
            heure_fermeture=datetime.time(20, 0),
            pause_debut=datetime.time(12, 30),
            pause_fin=datetime.time(14, 30),
        )
        assert horaire.est_ouvert_a(datetime.time(15, 0)) is True
        assert horaire.est_ouvert_a(datetime.time(14, 31)) is True

    def test_str_avec_pause(self):
        horaire = HoraireAvecPauseFactory()
        assert "/" in str(horaire)


# ─────────────────────────────────────────────────────────────────────────────
# FONCTION est_ouverte_maintenant()
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestEstOuverteMaintenant:

    def test_ouvert_selon_horaire_semaine(self):
        from apps.horaires.models import est_ouverte_maintenant

        pharmacie  = PharmacieActiveFactory()
        now        = timezone.localtime(timezone.now())
        jour_actuel = now.weekday()

        HoraireSemaineFactory(
            pharmacie=pharmacie,
            jour=jour_actuel,
            heure_ouverture=datetime.time(0, 0),
            heure_fermeture=datetime.time(23, 59),
            est_ferme=False,
        )
        assert est_ouverte_maintenant(pharmacie) is True

    def test_ferme_selon_horaire_semaine(self):
        from apps.horaires.models import est_ouverte_maintenant

        pharmacie   = PharmacieActiveFactory()
        now         = timezone.localtime(timezone.now())
        jour_actuel = now.weekday()

        HoraireFermeFactory(pharmacie=pharmacie, jour=jour_actuel)
        assert est_ouverte_maintenant(pharmacie) is False

    def test_exceptionnel_prime_sur_semaine(self):
        """Un horaire exceptionnel doit primer sur l'horaire hebdomadaire."""
        from apps.horaires.models import est_ouverte_maintenant

        pharmacie   = PharmacieActiveFactory()
        now         = timezone.localtime(timezone.now())
        jour_actuel = now.weekday()

        # Horaire semaine : ouvert toute la journée
        HoraireSemaineFactory(
            pharmacie=pharmacie,
            jour=jour_actuel,
            heure_ouverture=datetime.time(0, 0),
            heure_fermeture=datetime.time(23, 59),
        )

        # Horaire exceptionnel aujourd'hui : FERMÉ
        HoraireExceptionnelFactory(
            pharmacie=pharmacie,
            date=now.date(),
            est_ferme=True,
        )

        # Résultat attendu : FERMÉ (exceptionnel prime)
        assert est_ouverte_maintenant(pharmacie) is False

    def test_exceptionnel_ouvert_prime_sur_fermeture(self):
        """Horaire exceptionnel ouvert prime même si semaine fermé."""
        from apps.horaires.models import est_ouverte_maintenant

        pharmacie   = PharmacieActiveFactory()
        now         = timezone.localtime(timezone.now())
        jour_actuel = now.weekday()

        # Semaine : fermé ce jour
        HoraireFermeFactory(pharmacie=pharmacie, jour=jour_actuel)

        # Exceptionnel aujourd'hui : ouvert toute la journée
        HoraireExceptionnelOuvertFactory(
            pharmacie=pharmacie,
            date=now.date(),
            est_ferme=False,
            heure_ouverture=datetime.time(0, 0),
            heure_fermeture=datetime.time(23, 59),
        )

        assert est_ouverte_maintenant(pharmacie) is True

    def test_pas_d_horaire_defini(self):
        """Sans horaire défini, la pharmacie est considérée fermée."""
        from apps.horaires.models import est_ouverte_maintenant

        pharmacie = PharmacieActiveFactory()
        assert est_ouverte_maintenant(pharmacie) is False


# ─────────────────────────────────────────────────────────────────────────────
# SERIALIZER — BULK UPDATE
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestHoraireBulkSerializer:

    def test_bulk_cree_7_jours(self):
        pharmacie = PharmacieActiveFactory()

        from apps.horaires.serializers import HoraireSemaineBulkSerializer

        horaires_data = [
            {
                "jour": j,
                "heure_ouverture": "08:00:00",
                "heure_fermeture": "20:00:00",
                "est_ferme": False,
            }
            for j in range(6)  # Lundi à Samedi
        ]
        horaires_data.append({"jour": 6, "est_ferme": True})  # Dimanche fermé

        serializer = HoraireSemaineBulkSerializer(
            data={"horaires": horaires_data},
            context={"pharmacie": pharmacie},
        )
        assert serializer.is_valid(), serializer.errors
        resultats = serializer.save()

        assert resultats["crees"] == 7

        from apps.horaires.models import HoraireSemaine
        assert HoraireSemaine.objects.filter(pharmacie=pharmacie).count() == 7

    def test_bulk_idempotent(self):
        """Appeler bulk deux fois ne doit pas créer de doublons."""
        pharmacie = PharmacieActiveFactory()
        from apps.horaires.serializers import HoraireSemaineBulkSerializer
        from apps.horaires.models import HoraireSemaine

        data = {"horaires": [
            {"jour": 0, "heure_ouverture": "08:00:00",
             "heure_fermeture": "20:00:00", "est_ferme": False}
        ]}

        for _ in range(2):
            s = HoraireSemaineBulkSerializer(
                data=data, context={"pharmacie": pharmacie}
            )
            s.is_valid()
            s.save()

        assert HoraireSemaine.objects.filter(pharmacie=pharmacie, jour=0).count() == 1

    def test_bulk_jour_duplique_invalide(self):
        """Deux entrées pour le même jour doivent échouer la validation."""
        pharmacie = PharmacieActiveFactory()
        from apps.horaires.serializers import HoraireSemaineBulkSerializer

        data = {"horaires": [
            {"jour": 0, "heure_ouverture": "08:00:00",
             "heure_fermeture": "20:00:00", "est_ferme": False},
            {"jour": 0, "est_ferme": True},  # doublon
        ]}
        serializer = HoraireSemaineBulkSerializer(
            data=data, context={"pharmacie": pharmacie}
        )
        assert serializer.is_valid() is False

    def test_validation_ouverture_apres_fermeture(self):
        """heure_ouverture >= heure_fermeture doit échouer."""
        pharmacie = PharmacieActiveFactory()
        from apps.horaires.serializers import HoraireSemaineBulkSerializer

        data = {"horaires": [
            {"jour": 0, "heure_ouverture": "20:00:00",
             "heure_fermeture": "08:00:00", "est_ferme": False},
        ]}
        serializer = HoraireSemaineBulkSerializer(
            data=data, context={"pharmacie": pharmacie}
        )
        assert serializer.is_valid() is False

    def test_validation_pause_incomplete(self):
        """pause_debut sans pause_fin doit échouer."""
        pharmacie = PharmacieActiveFactory()
        from apps.horaires.serializers import HoraireSemaineBulkSerializer

        data = {"horaires": [
            {
                "jour": 0,
                "heure_ouverture": "08:00:00",
                "heure_fermeture": "20:00:00",
                "pause_debut": "12:30:00",
                # pause_fin manquant
                "est_ferme": False,
            },
        ]}
        serializer = HoraireSemaineBulkSerializer(
            data=data, context={"pharmacie": pharmacie}
        )
        assert serializer.is_valid() is False