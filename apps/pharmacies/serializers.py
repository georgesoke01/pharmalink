# apps/pharmacies/serializers.py
from rest_framework import serializers
from .models import Pharmacie
from .filters import SERVICES_DISPONIBLES


class PharmaciePublicSerializer(serializers.ModelSerializer):
    """Lecture publique — app mobile (liste des pharmacies).
    Données minimales pour l'affichage sur la carte.
    """

    coordonnees  = serializers.ReadOnlyField()
    est_active   = serializers.ReadOnlyField()
    pharmacien_nom = serializers.SerializerMethodField()

    class Meta:
        model  = Pharmacie
        fields = [
            "id", "nom", "adresse", "ville", "telephone",
            "latitude", "longitude", "coordonnees",
            "est_ouverte", "est_de_garde", "est_active",
            "services", "logo",
            "pharmacien_nom",
        ]

    def get_pharmacien_nom(self, obj) -> str:
        return obj.pharmacien.nom_complet


class PharmacieDetailSerializer(serializers.ModelSerializer):
    """Lecture détaillée — fiche complète d'une pharmacie (app mobile)."""

    coordonnees    = serializers.ReadOnlyField()
    est_active     = serializers.ReadOnlyField()
    pharmacien_nom = serializers.SerializerMethodField()

    class Meta:
        model  = Pharmacie
        fields = [
            "id", "nom", "numero_agrement", "siret",
            "description", "logo", "services",
            "adresse", "ville", "code_postal",
            "telephone", "email", "site_web",
            "latitude", "longitude", "coordonnees",
            "statut", "est_ouverte", "est_de_garde", "est_active",
            "pharmacien_nom",
            "created_at", "updated_at",
        ]

    def get_pharmacien_nom(self, obj) -> str:
        return obj.pharmacien.nom_complet


class PharmacieCreateSerializer(serializers.ModelSerializer):
    """Création d'une pharmacie par un pharmacien."""

    class Meta:
        model  = Pharmacie
        fields = [
            "nom", "numero_agrement", "siret", "description", "logo",
            "services", "adresse", "ville", "code_postal",
            "telephone", "email", "site_web",
            "latitude", "longitude",
        ]

    def validate_services(self, value: list) -> list:
        """Vérifie que tous les services fournis sont dans la liste autorisée."""
        invalides = [s for s in value if s not in SERVICES_DISPONIBLES]
        if invalides:
            raise serializers.ValidationError(
                f"Services invalides : {invalides}. "
                f"Choix possibles : {SERVICES_DISPONIBLES}"
            )
        return value

    def validate_numero_agrement(self, value: str) -> str:
        """Vérifie l'unicité du numéro d'agrément."""
        if value and Pharmacie.objects.filter(numero_agrement=value).exists():
            raise serializers.ValidationError(
                "Ce numéro d'agrément est déjà enregistré."
            )
        return value

    def create(self, validated_data):
        """Associe automatiquement le pharmacien connecté."""
        validated_data["pharmacien"] = self.context["request"].user
        return super().create(validated_data)


class PharmacieUpdateSerializer(serializers.ModelSerializer):
    """Mise à jour d'une pharmacie par son pharmacien."""

    class Meta:
        model  = Pharmacie
        fields = [
            "nom", "description", "logo", "services",
            "adresse", "ville", "code_postal",
            "telephone", "email", "site_web",
            "latitude", "longitude",
        ]

    def validate_services(self, value: list) -> list:
        invalides = [s for s in value if s not in SERVICES_DISPONIBLES]
        if invalides:
            raise serializers.ValidationError(
                f"Services invalides : {invalides}. "
                f"Choix possibles : {SERVICES_DISPONIBLES}"
            )
        return value


class PharmacieAdminSerializer(serializers.ModelSerializer):
    """Serializer admin — vue complète avec statut modifiable."""

    coordonnees  = serializers.ReadOnlyField()
    pharmacien_info = serializers.SerializerMethodField()

    class Meta:
        model  = Pharmacie
        fields = [
            "id", "nom", "numero_agrement", "siret",
            "description", "logo", "services",
            "adresse", "ville", "code_postal",
            "telephone", "email", "site_web",
            "latitude", "longitude", "coordonnees",
            "statut", "est_ouverte", "est_de_garde",
            "pharmacien", "pharmacien_info",
            "created_at", "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at", "pharmacien"]

    def get_pharmacien_info(self, obj) -> dict:
        return {
            "id":       obj.pharmacien.id,
            "username": obj.pharmacien.username,
            "email":    obj.pharmacien.email,
            "nom":      obj.pharmacien.nom_complet,
        }


class AdminStatutSerializer(serializers.Serializer):
    """Changement de statut d'une pharmacie par le super admin."""

    action = serializers.ChoiceField(choices=["activer", "suspendre"])
    raison = serializers.CharField(required=False, allow_blank=True, default="")

    def save(self):
        pharmacie = self.context["pharmacie"]
        admin     = self.context["request"].user
        action    = self.validated_data["action"]

        if action == "activer":
            pharmacie.activer(admin)
        else:
            pharmacie.suspendre(self.validated_data.get("raison", ""))
        return pharmacie