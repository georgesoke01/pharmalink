# apps/gardes/serializers.py
from django.utils import timezone
from rest_framework import serializers
from .models import PeriodeGarde


class PeriodeGardePublicSerializer(serializers.ModelSerializer):
    """Lecture publique — app mobile."""

    pharmacie_nom     = serializers.ReadOnlyField(source="pharmacie.nom")
    pharmacie_adresse = serializers.ReadOnlyField(source="pharmacie.adresse")
    pharmacie_ville   = serializers.ReadOnlyField(source="pharmacie.ville")
    telephone_effectif = serializers.ReadOnlyField()
    est_active_maintenant = serializers.ReadOnlyField()

    class Meta:
        model  = PeriodeGarde
        fields = [
            "id", "pharmacie", "pharmacie_nom",
            "pharmacie_adresse", "pharmacie_ville",
            "date_debut", "date_fin",
            "telephone_effectif",
            "zone_ville", "zone_quartier",
            "note", "statut",
            "est_active_maintenant",
        ]


class PeriodeGardeCreateSerializer(serializers.ModelSerializer):
    """Création d'une garde par un pharmacien."""

    class Meta:
        model  = PeriodeGarde
        fields = [
            "date_debut", "date_fin",
            "telephone_garde",
            "zone_ville", "zone_quartier",
            "note",
        ]

    def validate(self, data):
        debut = data.get("date_debut")
        fin   = data.get("date_fin")

        if debut and fin:
            if debut >= fin:
                raise serializers.ValidationError(
                    {"date_fin": "La date de fin doit être après la date de début."}
                )
            if debut < timezone.now():
                raise serializers.ValidationError(
                    {"date_debut": "La date de début ne peut pas être dans le passé."}
                )

        # Vérifie chevauchement avec gardes existantes de la même pharmacie
        pharmacie = self.context.get("pharmacie")
        if pharmacie and debut and fin:
            chevauchement = PeriodeGarde.objects.filter(
                pharmacie=pharmacie,
                statut__in=[PeriodeGarde.Statut.PLANIFIEE, PeriodeGarde.Statut.EN_COURS],
                date_debut__lt=fin,
                date_fin__gt=debut,
            )
            if self.instance:
                chevauchement = chevauchement.exclude(pk=self.instance.pk)
            if chevauchement.exists():
                raise serializers.ValidationError(
                    "Cette période chevauche une garde déjà déclarée pour cette pharmacie."
                )
        return data

    def create(self, validated_data):
        validated_data["pharmacie"] = self.context["pharmacie"]
        return super().create(validated_data)


class PeriodeGardeUpdateSerializer(serializers.ModelSerializer):
    """Mise à jour d'une garde (uniquement si PLANIFIEE)."""

    class Meta:
        model  = PeriodeGarde
        fields = [
            "date_debut", "date_fin",
            "telephone_garde",
            "zone_ville", "zone_quartier",
            "note",
        ]

    def validate(self, data):
        if self.instance and self.instance.statut != PeriodeGarde.Statut.PLANIFIEE:
            raise serializers.ValidationError(
                "Seules les gardes planifiées peuvent être modifiées."
            )
        debut = data.get("date_debut", getattr(self.instance, "date_debut", None))
        fin   = data.get("date_fin",   getattr(self.instance, "date_fin",   None))
        if debut and fin and debut >= fin:
            raise serializers.ValidationError(
                {"date_fin": "La date de fin doit être après la date de début."}
            )
        return data


class PeriodeGardeAdminSerializer(serializers.ModelSerializer):
    """Vue admin complète avec tous les champs."""

    pharmacie_nom  = serializers.ReadOnlyField(source="pharmacie.nom")
    est_active_maintenant = serializers.ReadOnlyField()
    est_passee     = serializers.ReadOnlyField()
    est_a_venir    = serializers.ReadOnlyField()

    class Meta:
        model  = PeriodeGarde
        fields = [
            "id", "pharmacie", "pharmacie_nom",
            "date_debut", "date_fin",
            "telephone_garde", "telephone_effectif",
            "zone_ville", "zone_quartier",
            "statut", "note",
            "est_active_maintenant", "est_passee", "est_a_venir",
            "created_at",
        ]
        read_only_fields = ["created_at", "telephone_effectif"]