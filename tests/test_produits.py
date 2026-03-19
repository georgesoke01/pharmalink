# tests/test_produits.py
"""
Tests unitaires — apps/produits/

Couvre :
    - Modèle Produit, Stock, Prix
    - Propriétés (est_en_alerte, est_en_rupture)
    - save() automatique (disponible=False si quantite=0)
    - BulkUpdate serializers
"""
import pytest
from tests.factories import (
    ProduitFactory,
    ProduitOrdonanceFactory,
    StockFactory,
    StockVideFactory,
    StockEnAlerteFactory,
    PrixFactory,
    PharmacieActiveFactory,
)


# ─────────────────────────────────────────────────────────────────────────────
# MODÈLE PRODUIT
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestProduitModele:

    def test_creation_produit_standard(self):
        produit = ProduitFactory()
        assert produit.pk          is not None
        assert produit.categorie   == "medicament"
        assert produit.sur_ordonnance is False

    def test_produit_sur_ordonnance(self):
        produit = ProduitOrdonanceFactory()
        assert produit.sur_ordonnance is True
        assert "Ordonnance" in str(produit) or "📋" in str(produit)

    def test_str_inclut_nom(self):
        produit = ProduitFactory(nom="Doliprane", dosage="500mg")
        assert "Doliprane" in str(produit)
        assert "500mg"     in str(produit)

    def test_code_cip13_indexe(self):
        """Le code CIP13 doit être indexé pour les recherches rapides."""
        from apps.produits.models import Produit
        index_names = [
            idx.name for idx in Produit._meta.indexes
        ]
        # db_index=True crée un index sans nom explicite
        # On vérifie juste que le champ a db_index
        field = Produit._meta.get_field("code_cip13")
        assert field.db_index is True


# ─────────────────────────────────────────────────────────────────────────────
# MODÈLE STOCK
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestStockModele:

    def test_stock_disponible_par_defaut(self):
        stock = StockFactory(quantite=100)
        assert stock.disponible      is True
        assert stock.est_en_rupture  is False
        assert stock.est_en_alerte   is False

    def test_stock_vide_devient_indisponible(self):
        """save() doit passer disponible=False automatiquement si quantite=0."""
        stock = StockFactory(quantite=10)
        stock.quantite = 0
        stock.save()
        stock.refresh_from_db()

        assert stock.disponible     is False
        assert stock.est_en_rupture is True

    def test_stock_remis_disponible_si_quantite_positive(self):
        """save() doit repasser disponible=True si quantite revient > 0."""
        stock = StockVideFactory()    # quantite=0, disponible=False
        assert stock.disponible is False

        stock.quantite = 50
        stock.save()
        stock.refresh_from_db()

        assert stock.disponible is True

    def test_stock_remis_disponible_si_quantite_positive(self):
        """save() doit repasser disponible=True si quantite revient > 0."""
        stock = StockVideFactory()    # quantite=0, disponible=False
        assert stock.disponible is False

        stock.quantite = 50
        stock.save()
        stock.refresh_from_db()

        assert stock.disponible is True

    def test_stock_en_alerte(self):
        stock = StockEnAlerteFactory()
        assert stock.est_en_alerte  is True
        assert stock.est_en_rupture is False

    def test_stock_seuil_alerte_zero_pas_dalerte(self):
        """Seuil à 0 = alertes désactivées."""
        stock = StockFactory(quantite=5, seuil_alerte=0)
        assert stock.est_en_alerte is False

    def test_stock_unique_par_pharmacie_produit(self):
        from django.db import IntegrityError
        from apps.produits.models import Stock

        pharmacie = PharmacieActiveFactory()
        produit   = ProduitFactory()

        StockFactory(pharmacie=pharmacie, produit=produit, quantite=10)

        with pytest.raises(IntegrityError):
            Stock.objects.create(
                pharmacie=pharmacie,
                produit=produit,
                quantite=20,
            )

    def test_str_inclut_pharmacie_et_produit(self):
        stock = StockFactory()
        assert stock.pharmacie.nom in str(stock)
        assert stock.produit.nom   in str(stock)


# ─────────────────────────────────────────────────────────────────────────────
# MODÈLE PRIX
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestPrixModele:

    def test_prix_en_fcfa(self):
        prix = PrixFactory(prix_fcfa=2500)
        assert prix.prix_fcfa == 2500
        assert "FCFA"         in str(prix)

    def test_prix_unique_par_pharmacie_produit(self):
        from django.db import IntegrityError
        from apps.produits.models import Prix

        pharmacie = PharmacieActiveFactory()
        produit   = ProduitFactory()

        PrixFactory(pharmacie=pharmacie, produit=produit, prix_fcfa=2500)

        with pytest.raises(IntegrityError):
            Prix.objects.create(
                pharmacie=pharmacie,
                produit=produit,
                prix_fcfa=3000,
            )


# ─────────────────────────────────────────────────────────────────────────────
# SERIALIZER — BULK UPDATE
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestBulkUpdateSerializers:

    def test_bulk_stock_update(self):
        pharmacie = PharmacieActiveFactory()
        produit1  = ProduitFactory()
        produit2  = ProduitFactory()

        from apps.produits.serializers import StockBulkUpdateSerializer

        # Les deux items ont seuil_alerte avec default=0 dans le serializer
        data = {
            "stocks": [
                {"produit_id": produit1.pk, "quantite": 50, "seuil_alerte": 10},
                {"produit_id": produit2.pk, "quantite": 0,  "seuil_alerte": 0},
            ]
        }
        serializer = StockBulkUpdateSerializer(
            data=data,
            context={"pharmacie": pharmacie},
        )
        is_valid = serializer.is_valid()
        assert is_valid, f"Erreurs serializer bulk stock: {serializer.errors}"
        results = serializer.save()

        assert results["mis_a_jour"] == 2
        assert results["erreurs"]    == []

        from apps.produits.models import Stock
        s1 = Stock.objects.get(pharmacie=pharmacie, produit=produit1)
        s2 = Stock.objects.get(pharmacie=pharmacie, produit=produit2)

        assert s1.quantite   == 50
        assert s1.disponible is True
        assert s2.quantite   == 0
        assert s2.disponible is False

    def test_bulk_stock_idempotent(self):
        """Appeler bulk deux fois ne crée pas de doublons."""
        pharmacie = PharmacieActiveFactory()
        produit   = ProduitFactory()

        from apps.produits.serializers import StockBulkUpdateSerializer
        from apps.produits.models import Stock

        data = {"stocks": [{"produit_id": produit.pk, "quantite": 30}]}

        for _ in range(2):
            s = StockBulkUpdateSerializer(
                data=data, context={"pharmacie": pharmacie}
            )
            s.is_valid()
            s.save()

        assert Stock.objects.filter(pharmacie=pharmacie, produit=produit).count() == 1

    def test_bulk_prix_update(self):
        pharmacie = PharmacieActiveFactory()
        produit1  = ProduitFactory()
        produit2  = ProduitFactory()

        from apps.produits.serializers import PrixBulkUpdateSerializer

        data = {
            "prix": [
                {"produit_id": produit1.pk, "prix_fcfa": 2500},
                {"produit_id": produit2.pk, "prix_fcfa": 800},
            ]
        }
        serializer = PrixBulkUpdateSerializer(
            data=data, context={"pharmacie": pharmacie}
        )
        assert serializer.is_valid(), serializer.errors
        results = serializer.save()

        assert results["mis_a_jour"] == 2

        from apps.produits.models import Prix
        p1 = Prix.objects.get(pharmacie=pharmacie, produit=produit1)
        assert p1.prix_fcfa == 2500

    def test_bulk_prix_validation_prix_negatif(self):
        pharmacie = PharmacieActiveFactory()
        produit   = ProduitFactory()

        from apps.produits.serializers import PrixBulkUpdateSerializer

        data = {"prix": [{"produit_id": produit.pk, "prix_fcfa": 0}]}
        serializer = PrixBulkUpdateSerializer(
            data=data, context={"pharmacie": pharmacie}
        )
        assert serializer.is_valid() is False