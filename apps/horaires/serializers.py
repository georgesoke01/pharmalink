# apps/horaires/serializers.py
from rest_framework import serializers
from .models import HoraireSemaine, HoraireExceptionnel


class HoraireSemaineSerializer(serializers.ModelSerializer):
    """Lecture/écriture d'un horaire hebdomadaire."""

    jour_label = serializers.SerializerMethodField()

    class Meta:
        model  = HoraireSemaine
        fields = [
            "id", "jour", "jour_label",
            "heure_ouverture", "heure_fermeture",
            "pause_debut", "pause_fin",
            "est_ferme", "updated_at",
        ]
        read_only_fields = ["id", "updated_at"]

    def get_jour_label(self, obj) -> str:
        return obj.get_jour_display()

    def validate(self, data):
        est_ferme = data.get("est_ferme", getattr(self.instance, "est_ferme", False))

        if not est_ferme:
            if not data.get("heure_ouverture") and not getattr(self.instance, "heure_ouverture", None):
                raise serializers.ValidationError(
                    {"heure_ouverture": "Obligatoire si la pharmacie est ouverte."}
                )
            if not data.get("heure_fermeture") and not getattr(self.instance, "heure_fermeture", None):
                raise serializers.ValidationError(
                    {"heure_fermeture": "Obligatoire si la pharmacie est ouverte."}
                )

        pause_debut = data.get("pause_debut")
        pause_fin   = data.get("pause_fin")
        if (pause_debut and not pause_fin) or (pause_fin and not pause_debut):
            raise serializers.ValidationError(
                "pause_debut et pause_fin doivent être renseignés ensemble."
            )
        if pause_debut and pause_fin and pause_debut >= pause_fin:
            raise serializers.ValidationError(
                {"pause_fin": "La fin de pause doit être après le début."}
            )

        ouverture = data.get("heure_ouverture")
        fermeture = data.get("heure_fermeture")
        if ouverture and fermeture and ouverture >= fermeture:
            raise serializers.ValidationError(
                {"heure_fermeture": "L'heure de fermeture doit être après l'ouverture."}
            )
        return data


class HoraireSemaineBulkSerializer(serializers.Serializer):
    """Mise à jour des 7 jours d'une pharmacie en une seule requête.

    Body :
    {
        "horaires": [
            {"jour": 0, "heure_ouverture": "08:00", "heure_fermeture": "20:00"},
            {"jour": 1, "heure_ouverture": "08:00", "heure_fermeture": "20:00",
             "pause_debut": "12:30", "pause_fin": "14:30"},
            {"jour": 6, "est_ferme": true}
        ]
    }
    """

    horaires = HoraireSemaineSerializer(many=True)

    def validate_horaires(self, value):
        jours = [h["jour"] for h in value]
        if len(jours) != len(set(jours)):
            raise serializers.ValidationError(
                "Chaque jour ne peut apparaître qu'une seule fois."
            )
        return value

    def save(self):
        pharmacie = self.context["pharmacie"]
        resultats = {"crees": 0, "mis_a_jour": 0}

        for data in self.validated_data["horaires"]:
            _, created = HoraireSemaine.objects.update_or_create(
                pharmacie=pharmacie,
                jour=data["jour"],
                defaults={
                    "heure_ouverture": data.get("heure_ouverture"),
                    "heure_fermeture": data.get("heure_fermeture"),
                    "pause_debut":     data.get("pause_debut"),
                    "pause_fin":       data.get("pause_fin"),
                    "est_ferme":       data.get("est_ferme", False),
                },
            )
            if created:
                resultats["crees"] += 1
            else:
                resultats["mis_a_jour"] += 1

        return resultats


class HoraireExceptionnelSerializer(serializers.ModelSerializer):
    """Lecture/écriture d'un horaire exceptionnel."""

    class Meta:
        model  = HoraireExceptionnel
        fields = [
            "id", "date", "motif",
            "heure_ouverture", "heure_fermeture",
            "pause_debut", "pause_fin",
            "est_ferme",
        ]
        read_only_fields = ["id"]

    def validate(self, data):
        est_ferme = data.get("est_ferme", True)
        if not est_ferme:
            if not data.get("heure_ouverture"):
                raise serializers.ValidationError(
                    {"heure_ouverture": "Obligatoire si la pharmacie est ouverte ce jour."}
                )
            if not data.get("heure_fermeture"):
                raise serializers.ValidationError(
                    {"heure_fermeture": "Obligatoire si la pharmacie est ouverte ce jour."}
                )
        pause_debut = data.get("pause_debut")
        pause_fin   = data.get("pause_fin")
        if (pause_debut and not pause_fin) or (pause_fin and not pause_debut):
            raise serializers.ValidationError(
                "pause_debut et pause_fin doivent être renseignés ensemble."
            )
        return data


class HorairesCompletSerializer(serializers.Serializer):
    """Vue complète des horaires d'une pharmacie — app mobile.
    Combine semaine + exceptions + statut ouverture actuel.
    """

    semaine                = HoraireSemaineSerializer(many=True)
    exceptions             = HoraireExceptionnelSerializer(many=True)
    est_ouverte_maintenant = serializers.BooleanField()