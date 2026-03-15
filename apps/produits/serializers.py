# apps/produits/serializers.py
from rest_framework import serializers
from .models import Produit, Stock, Prix


# ─────────────────────────────────────────────────────────────────────────────
# PRODUIT
# ─────────────────────────────────────────────────────────────────────────────

class ProduitPublicSerializer(serializers.ModelSerializer):
    """Lecture publique — app mobile (liste et recherche)."""

    class Meta:
        model  = Produit
        fields = [
            "id", "nom", "nom_generique", "laboratoire",
            "categorie", "forme", "dosage",
            "sur_ordonnance", "image",
        ]


class ProduitDetailSerializer(serializers.ModelSerializer):
    """Fiche complète d'un produit — app mobile."""

    class Meta:
        model  = Produit
        fields = [
            "id", "code_cip13", "nom", "nom_generique",
            "laboratoire", "categorie", "forme", "dosage",
            "sur_ordonnance", "contre_indications",
            "description", "image",
            "created_at", "updated_at",
        ]


class ProduitCreateSerializer(serializers.ModelSerializer):
    """Création d'un produit — pharmacien ou admin."""

    class Meta:
        model  = Produit
        fields = [
            "code_cip13", "nom", "nom_generique",
            "laboratoire", "categorie", "forme", "dosage",
            "sur_ordonnance", "contre_indications",
            "description", "image",
        ]

    def validate_code_cip13(self, value):
        """Vérifie le format CIP13 si fourni (13 chiffres)."""
        if value and (len(value) != 13 or not value.isdigit()):
            raise serializers.ValidationError(
                "Le code CIP13 doit contenir exactement 13 chiffres."
            )
        return value


class ProduitUpdateSerializer(serializers.ModelSerializer):
    """Mise à jour d'un produit."""

    class Meta:
        model  = Produit
        fields = [
            "nom", "nom_generique", "laboratoire",
            "categorie", "forme", "dosage",
            "sur_ordonnance", "contre_indications",
            "description", "image",
        ]


# ─────────────────────────────────────────────────────────────────────────────
# STOCK
# ─────────────────────────────────────────────────────────────────────────────

class StockSerializer(serializers.ModelSerializer):
    """Stock d'un produit dans une pharmacie — lecture."""

    produit_nom      = serializers.ReadOnlyField(source="produit.nom")
    produit_image    = serializers.ImageField(source="produit.image", read_only=True)
    sur_ordonnance   = serializers.ReadOnlyField(source="produit.sur_ordonnance")
    est_en_alerte    = serializers.ReadOnlyField()
    est_en_rupture   = serializers.ReadOnlyField()
    prix_fcfa        = serializers.SerializerMethodField()

    class Meta:
        model  = Stock
        fields = [
            "id", "produit", "produit_nom", "produit_image",
            "sur_ordonnance", "quantite", "disponible",
            "seuil_alerte", "est_en_alerte", "est_en_rupture",
            "prix_fcfa", "updated_at",
        ]

    def get_prix_fcfa(self, obj) -> int | None:
        """Retourne le prix FCFA du produit dans cette pharmacie."""
        try:
            return Prix.objects.get(
                pharmacie=obj.pharmacie,
                produit=obj.produit,
            ).prix_fcfa
        except Prix.DoesNotExist:
            return None


class StockUpdateSerializer(serializers.ModelSerializer):
    """Mise à jour du stock par le pharmacien."""

    class Meta:
        model  = Stock
        fields = ["quantite", "disponible", "seuil_alerte"]

    def validate_quantite(self, value):
        if value < 0:
            raise serializers.ValidationError("La quantité ne peut pas être négative.")
        return value


class StockBulkUpdateSerializer(serializers.Serializer):
    """Mise à jour en masse du stock — utilisé lors de l'import LGO.

    Body :
    {
        "stocks": [
            {"produit_id": 1, "quantite": 50, "seuil_alerte": 10},
            {"produit_id": 2, "quantite": 0}
        ]
    }
    """

    class StockItemSerializer(serializers.Serializer):
        produit_id   = serializers.IntegerField()
        quantite     = serializers.IntegerField(min_value=0)
        seuil_alerte = serializers.IntegerField(min_value=0, default=0)

    stocks = StockItemSerializer(many=True)

    def save(self):
        pharmacie = self.context["pharmacie"]
        results   = {"mis_a_jour": 0, "erreurs": []}

        for item in self.validated_data["stocks"]:
            try:
                stock, _ = Stock.objects.get_or_create(
                    pharmacie=pharmacie,
                    produit_id=item["produit_id"],
                )
                stock.quantite     = item["quantite"]
                stock.seuil_alerte = item.get("seuil_alerte", 0)
                stock.save()
                results["mis_a_jour"] += 1
            except Exception as e:
                results["erreurs"].append(
                    f"produit_id={item['produit_id']} : {str(e)}"
                )

        return results


# ─────────────────────────────────────────────────────────────────────────────
# PRIX
# ─────────────────────────────────────────────────────────────────────────────

class PrixSerializer(serializers.ModelSerializer):
    """Prix d'un produit dans une pharmacie."""

    produit_nom = serializers.ReadOnlyField(source="produit.nom")

    class Meta:
        model  = Prix
        fields = ["id", "produit", "produit_nom", "prix_fcfa", "updated_at"]


class PrixUpdateSerializer(serializers.ModelSerializer):
    """Mise à jour du prix par le pharmacien."""

    class Meta:
        model  = Prix
        fields = ["prix_fcfa"]

    def validate_prix_fcfa(self, value):
        if value <= 0:
            raise serializers.ValidationError("Le prix doit être supérieur à 0 FCFA.")
        return value


class PrixBulkUpdateSerializer(serializers.Serializer):
    """Mise à jour en masse des prix — import LGO.

    Body :
    {
        "prix": [
            {"produit_id": 1, "prix_fcfa": 2500},
            {"produit_id": 2, "prix_fcfa": 800}
        ]
    }
    """

    class PrixItemSerializer(serializers.Serializer):
        produit_id = serializers.IntegerField()
        prix_fcfa  = serializers.IntegerField(min_value=1)

    prix = PrixItemSerializer(many=True)

    def save(self):
        pharmacie = self.context["pharmacie"]
        results   = {"mis_a_jour": 0, "erreurs": []}

        for item in self.validated_data["prix"]:
            try:
                Prix.objects.update_or_create(
                    pharmacie=pharmacie,
                    produit_id=item["produit_id"],
                    defaults={"prix_fcfa": item["prix_fcfa"]},
                )
                results["mis_a_jour"] += 1
            except Exception as e:
                results["erreurs"].append(
                    f"produit_id={item['produit_id']} : {str(e)}"
                )

        return results


# ─────────────────────────────────────────────────────────────────────────────
# VUE COMBINÉE — APP MOBILE
# ─────────────────────────────────────────────────────────────────────────────

class ProduitAvecPrixStockSerializer(serializers.ModelSerializer):
    """Produit avec son prix et stock dans une pharmacie donnée.
    Utilisé par l'app mobile pour la fiche d'une pharmacie.
    """

    prix_fcfa    = serializers.SerializerMethodField()
    disponible   = serializers.SerializerMethodField()
    quantite     = serializers.SerializerMethodField()

    class Meta:
        model  = Produit
        fields = [
            "id", "nom", "nom_generique", "forme", "dosage",
            "categorie", "sur_ordonnance", "image",
            "prix_fcfa", "disponible", "quantite",
        ]

    def _get_pharmacie_id(self):
        request = self.context.get("request")
        return request.query_params.get("pharmacie_id") if request else None

    def get_prix_fcfa(self, obj) -> int | None:
        pharmacie_id = self._get_pharmacie_id()
        if not pharmacie_id:
            return None
        try:
            return Prix.objects.get(
                pharmacie_id=pharmacie_id, produit=obj
            ).prix_fcfa
        except Prix.DoesNotExist:
            return None

    def get_disponible(self, obj) -> bool | None:
        pharmacie_id = self._get_pharmacie_id()
        if not pharmacie_id:
            return None
        try:
            return Stock.objects.get(
                pharmacie_id=pharmacie_id, produit=obj
            ).disponible
        except Stock.DoesNotExist:
            return None

    def get_quantite(self, obj) -> int | None:
        pharmacie_id = self._get_pharmacie_id()
        if not pharmacie_id:
            return None
        try:
            return Stock.objects.get(
                pharmacie_id=pharmacie_id, produit=obj
            ).quantite
        except Stock.DoesNotExist:
            return None