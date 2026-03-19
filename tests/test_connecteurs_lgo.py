# tests/test_connecteurs_lgo.py
"""
Tests unitaires — apps/connecteurs_lgo/
"""
import pytest
from unittest.mock import patch, MagicMock
from datetime import timedelta
from django.utils import timezone

from tests.factories import (
    ConnexionLGOFactory,
    ConnexionLGOErreurFactory,
    PharmacieActiveFactory,
    ProduitFactory,
    UserPharmacienApprouveFactory,
)


# ─────────────────────────────────────────────────────────────────────────────
# MODÈLE CONNEXION LGO
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestConnexionLGOModele:

    def test_marquer_succes(self):
        connexion = ConnexionLGOErreurFactory()
        assert connexion.statut == "erreur"

        connexion.marquer_succes()
        connexion.refresh_from_db()

        assert connexion.statut          == "active"
        assert connexion.nb_syncs_ok     >= 1
        assert connexion.derniere_erreur == ""
        assert connexion.derniere_sync   is not None

    def test_marquer_erreur(self):
        connexion = ConnexionLGOFactory()
        assert connexion.statut == "active"

        connexion.marquer_erreur("Fichier DB introuvable.")
        connexion.refresh_from_db()

        assert connexion.statut          == "erreur"
        assert connexion.nb_syncs_erreur >= 1
        assert "introuvable"             in connexion.derniere_erreur

    def test_taux_succes_calcul(self):
        connexion = ConnexionLGOFactory(nb_syncs_ok=8, nb_syncs_erreur=2)
        assert connexion.taux_succes == 0.8

    def test_taux_succes_zero_si_aucune_sync(self):
        connexion = ConnexionLGOFactory(nb_syncs_ok=0, nb_syncs_erreur=0)
        assert connexion.taux_succes == 0.0

    def test_str_inclut_pharmacie_et_lgo(self):
        connexion = ConnexionLGOFactory()
        assert connexion.pharmacie.nom          in str(connexion)
        assert connexion.get_type_lgo_display() in str(connexion)

    def test_one_to_one_avec_pharmacie(self):
        from apps.connecteurs_lgo.models import ConnexionLGO
        from django.db import IntegrityError

        pharmacie = PharmacieActiveFactory()
        ConnexionLGOFactory(pharmacie=pharmacie)

        with pytest.raises(IntegrityError):
            ConnexionLGO.objects.create(
                pharmacie=pharmacie,
                type_lgo="winpharma",
                config={},
            )


# ─────────────────────────────────────────────────────────────────────────────
# BASE CONNECTOR — synchroniser()
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestBaseConnectorSynchroniser:

    def _make_connecteur(self, produits):
        """Crée un connecteur concret minimal pour les tests."""
        from apps.connecteurs_lgo.base_connector import BaseConnecteurLGO

        class ConnecteurTest(BaseConnecteurLGO):
            def tester_connexion(self):
                return True
            def extraire_produits(self):
                return produits

        return ConnecteurTest(config={})

    def test_synchroniser_cree_produits_stocks_prix(self):
        from apps.connecteurs_lgo.base_connector import ProduitLGO

        pharmacie  = PharmacieActiveFactory()
        produits   = [
            ProduitLGO(
                code_cip13="1234567890123",
                nom="Doliprane 500mg",
                quantite_stock=100,
                prix_fcfa=2500,
                laboratoire="Sanofi",
                sur_ordonnance=False,
            ),
            ProduitLGO(
                code_cip13="9876543210987",
                nom="Amoxicilline 500mg",
                quantite_stock=50,
                prix_fcfa=3500,
                sur_ordonnance=True,
            ),
        ]
        connecteur = self._make_connecteur(produits)
        stats      = connecteur.synchroniser(pharmacie.pk)

        assert stats["produits"] == 2
        assert stats["stocks"]   == 2
        assert stats["prix"]     == 2
        assert stats["erreurs"]  == []
        assert stats["duree"]    >= 0

        from apps.produits.models import Produit, Stock, Prix
        assert Produit.objects.filter(code_cip13="1234567890123").exists()
        assert Stock.objects.filter(pharmacie=pharmacie).count() == 2
        assert Prix.objects.filter(pharmacie=pharmacie).count()  == 2

    def test_synchroniser_idempotent(self):
        from apps.connecteurs_lgo.base_connector import ProduitLGO

        pharmacie  = PharmacieActiveFactory()
        produits   = [ProduitLGO(
            code_cip13="1111111111111",
            nom="Test Produit",
            quantite_stock=10,
            prix_fcfa=1000,
        )]
        connecteur = self._make_connecteur(produits)

        connecteur.synchroniser(pharmacie.pk)
        connecteur.synchroniser(pharmacie.pk)

        from apps.produits.models import Produit, Stock
        assert Produit.objects.filter(code_cip13="1111111111111").count() == 1
        assert Stock.objects.filter(pharmacie=pharmacie).count()          == 1

    def test_synchroniser_met_a_jour_stock_existant(self):
        from apps.connecteurs_lgo.base_connector import ProduitLGO

        pharmacie = PharmacieActiveFactory()
        produit   = ProduitFactory(code_cip13="2222222222222")
        produits  = [ProduitLGO(
            code_cip13="2222222222222",
            nom=produit.nom,
            quantite_stock=75,
            prix_fcfa=5000,
        )]
        connecteur = self._make_connecteur(produits)
        connecteur.synchroniser(pharmacie.pk)

        from apps.produits.models import Stock
        stock = Stock.objects.get(pharmacie=pharmacie, produit=produit)
        assert stock.quantite == 75


# ─────────────────────────────────────────────────────────────────────────────
# SERIALIZER DÉTECTION LGO
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestDetectionLGOSerializer:

    def test_detection_valide_pharmagest(self):
        from apps.connecteurs_lgo.serializers import DetectionLGOSerializer

        pharmacie = PharmacieActiveFactory()
        request   = MagicMock()
        request.user = pharmacie.pharmacien

        data = {
            "pharmacie_id": pharmacie.pk,
            "type_lgo":     "pharmagest",
            "version_lgo":  "8.2.1",
            "poste_nom":    "PC-01",
            "config": {
                "db_path": "C:\\Pharmagest\\Data\\pharma.db",
                "db_type": "sqlite",
            },
        }
        serializer = DetectionLGOSerializer(data=data, context={"request": request})
        assert serializer.is_valid(), serializer.errors

    def test_detection_config_sqlite_sans_db_path_invalide(self):
        from apps.connecteurs_lgo.serializers import DetectionLGOSerializer

        pharmacie = PharmacieActiveFactory()
        request   = MagicMock()
        request.user = pharmacie.pharmacien

        data = {
            "pharmacie_id": pharmacie.pk,
            "type_lgo":     "pharmagest",
            "config":       {"db_type": "sqlite"},
        }
        serializer = DetectionLGOSerializer(data=data, context={"request": request})
        assert serializer.is_valid() is False
        assert "config" in serializer.errors

    def test_detection_pharmacie_inconnue(self):
        from apps.connecteurs_lgo.serializers import DetectionLGOSerializer

        pharmacien = UserPharmacienApprouveFactory()
        request    = MagicMock()
        request.user = pharmacien

        data = {
            "pharmacie_id": 99999,
            "type_lgo":     "pharmagest",
            "config":       {"db_path": "test.db", "db_type": "sqlite"},
        }
        serializer = DetectionLGOSerializer(data=data, context={"request": request})
        assert serializer.is_valid() is False
        assert "pharmacie_id" in serializer.errors

    def test_detection_cree_connexion_lgo(self):
        from apps.connecteurs_lgo.serializers import DetectionLGOSerializer
        from apps.connecteurs_lgo.models import ConnexionLGO

        pharmacie = PharmacieActiveFactory()
        request   = MagicMock()
        request.user = pharmacie.pharmacien

        data = {
            "pharmacie_id": pharmacie.pk,
            "type_lgo":     "pharmagest",
            "version_lgo":  "8.2.1",
            "poste_nom":    "PC-TEST",
            "config":       {"db_path": "test.db", "db_type": "sqlite"},
        }
        serializer = DetectionLGOSerializer(data=data, context={"request": request})
        serializer.is_valid()
        connexion, created = serializer.save()

        assert created is True
        assert connexion.type_lgo     == "pharmagest"
        assert connexion.detecte_auto is True
        assert connexion.poste_nom    == "PC-TEST"
        assert ConnexionLGO.objects.filter(pharmacie=pharmacie).count() == 1


# ─────────────────────────────────────────────────────────────────────────────
# CONNECTEUR PHARMAGEST
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestConnecteurPharmagest:

    def test_tester_connexion_echec_si_db_absente(self):
        from apps.connecteurs_lgo.pharmagest import ConnecteurPharmagest

        connecteur = ConnecteurPharmagest(config={
            "db_path": "/chemin/inexistant/pharma.db",
            "db_type": "sqlite",
        })
        assert connecteur.tester_connexion() is False

    def test_extraire_produits_avec_mock_sqlite(self):
        from apps.connecteurs_lgo.pharmagest import ConnecteurPharmagest

        mock_rows = [
            {
                "code_cip13":     "1234567890123",
                "nom":            "Doliprane",
                "nom_generique":  "Paracétamol",
                "laboratoire":    "Sanofi",
                "categorie":      "MEDICAMENT",
                "forme":          "comprimés",
                "dosage":         "500mg",
                "sur_ordonnance": 0,
                "quantite_stock": 100,
                "prix_vente":     250,
            }
        ]

        connecteur = ConnecteurPharmagest(config={
            "db_path": "C:\\Pharmagest\\Data\\pharma.db",
            "db_type": "sqlite",
        })

        with patch.object(connecteur, "_get_connection") as mock_conn:
            mock_conn_obj = MagicMock()
            mock_conn_obj.execute.return_value.fetchall.return_value = mock_rows
            mock_conn_obj.close = MagicMock()
            mock_conn.return_value = mock_conn_obj

            produits = connecteur.extraire_produits()

        assert len(produits)              == 1
        assert produits[0].nom            == "Doliprane"
        assert produits[0].code_cip13     == "1234567890123"
        assert produits[0].sur_ordonnance is False
        assert produits[0].quantite_stock == 100
        assert produits[0].prix_fcfa      == pytest.approx(1639, abs=5)

    def test_mapper_categorie(self):
        from apps.connecteurs_lgo.pharmagest import ConnecteurPharmagest

        assert ConnecteurPharmagest._mapper_categorie("MEDICAMENT")    == "medicament"
        assert ConnecteurPharmagest._mapper_categorie("PARA")          == "parapharmacie"
        assert ConnecteurPharmagest._mapper_categorie("PARAPHARMACIE") == "parapharmacie"
        assert ConnecteurPharmagest._mapper_categorie("MATERIEL")      == "materiel"
        assert ConnecteurPharmagest._mapper_categorie("INCONNU")       == "autre"


# ─────────────────────────────────────────────────────────────────────────────
# TÂCHE CELERY — sync_pharmacie_lgo
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestCelerySync:

    def test_sync_skipped_si_pas_de_connexion_active(self):
        from apps.connecteurs_lgo.tasks import sync_pharmacie_lgo

        pharmacie = PharmacieActiveFactory()
        result    = sync_pharmacie_lgo(pharmacie.pk, "auto")

        assert result["status"] == "skipped"

    def test_sync_ok_avec_mock_connecteur(self):
        from apps.connecteurs_lgo.tasks import sync_pharmacie_lgo

        connexion  = ConnexionLGOFactory()
        mock_stats = {
            "produits": 5,
            "stocks":   5,
            "prix":     5,
            "erreurs":  [],
            "duree":    1.2,
        }

        # CONNECTEURS est un dict au niveau module → on patche le dict directement
        mock_connecteur = MagicMock()
        mock_connecteur.synchroniser.return_value = mock_stats

        with patch("apps.connecteurs_lgo.tasks.CONNECTEURS",
                   {"pharmagest": MagicMock(return_value=mock_connecteur)}):
            result = sync_pharmacie_lgo(connexion.pharmacie_id, "auto")

        assert result["status"]   == "ok"
        assert result["produits"] == 5

        connexion.refresh_from_db()
        assert connexion.statut      == "active"
        assert connexion.nb_syncs_ok >= 6

    def test_sync_marque_erreur_sur_exception(self):
        from apps.connecteurs_lgo.tasks import sync_pharmacie_lgo

        connexion = ConnexionLGOFactory()

        mock_connecteur = MagicMock()
        mock_connecteur.synchroniser.side_effect = Exception("DB corrompue")

        with patch("apps.connecteurs_lgo.tasks.CONNECTEURS",
                   {"pharmagest": MagicMock(return_value=mock_connecteur)}):
            with pytest.raises(Exception):
                sync_pharmacie_lgo(connexion.pharmacie_id, "auto")

        connexion.refresh_from_db()
        assert connexion.statut          == "erreur"
        assert connexion.nb_syncs_erreur >= 1