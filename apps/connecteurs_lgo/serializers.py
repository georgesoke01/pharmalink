# apps/connecteurs_lgo/serializers.py
from rest_framework import serializers
from .models import ConnexionLGO, LogSync


# ─────────────────────────────────────────────────────────────────────────────
# AUTO-DÉTECTION (envoyé par l'app Desktop Tauri)
# ─────────────────────────────────────────────────────────────────────────────

class DetectionLGOSerializer(serializers.Serializer):
    """Reçoit le résultat du scan automatique de l'app Desktop Tauri.

    Envoyé par Tauri immédiatement après détection et autorisation
    de l'utilisateur. Crée ou met à jour la ConnexionLGO.

    Body attendu :
    {
        "pharmacie_id": 3,
        "type_lgo": "pharmagest",
        "version_lgo": "8.2.1",
        "poste_nom": "PC-PHARMACIE-01",
        "config": {
            "db_path": "C:\\\\Pharmagest\\\\Data\\\\pharma.db",
            "db_type": "sqlite",
            "chemin_installation": "C:\\\\Pharmagest\\\\"
        }
    }
    """

    pharmacie_id = serializers.IntegerField()
    type_lgo     = serializers.ChoiceField(choices=ConnexionLGO.TypeLGO.choices)
    version_lgo  = serializers.CharField(max_length=50, default="", allow_blank=True)
    poste_nom    = serializers.CharField(max_length=100, default="", allow_blank=True)
    config       = serializers.DictField()

    def validate_pharmacie_id(self, value):
        from apps.pharmacies.models import Pharmacie
        user = self.context["request"].user
        try:
            Pharmacie.objects.get(pk=value, pharmacien=user, statut="active")
        except Pharmacie.DoesNotExist:
            raise serializers.ValidationError(
                "Pharmacie introuvable, inactive ou non autorisée."
            )
        return value

    def validate_config(self, value):
        """Vérifie que la config contient les champs minimaux."""
        db_type = value.get("db_type", "sqlite")
        if db_type == "sqlite" and not value.get("db_path"):
            raise serializers.ValidationError(
                "db_path est requis pour une base SQLite."
            )
        if db_type == "mysql" and not value.get("db_host"):
            raise serializers.ValidationError(
                "db_host est requis pour une base MySQL."
            )
        return value

    def save(self):
        data = self.validated_data
        connexion, created = ConnexionLGO.objects.update_or_create(
            pharmacie_id=data["pharmacie_id"],
            defaults={
                "type_lgo":    data["type_lgo"],
                "version_lgo": data.get("version_lgo", ""),
                "poste_nom":   data.get("poste_nom", ""),
                "config":      data["config"],
                "detecte_auto": True,
                "statut":      ConnexionLGO.Statut.INACTIVE,
            },
        )
        return connexion, created


class TestConnexionSerializer(serializers.Serializer):
    """Test de connexion au LGO depuis le serveur Django.

    Utilisé après la détection pour confirmer que l'API
    peut accéder à la DB du LGO.
    """
    pharmacie_id = serializers.IntegerField()


# ─────────────────────────────────────────────────────────────────────────────
# LECTURE — STATUT ET LOGS
# ─────────────────────────────────────────────────────────────────────────────

class ConnexionLGOSerializer(serializers.ModelSerializer):
    """Statut complet de la connexion LGO d'une pharmacie."""

    type_lgo_label  = serializers.ReadOnlyField(source="get_type_lgo_display")
    statut_label    = serializers.ReadOnlyField(source="get_statut_display")
    taux_succes     = serializers.ReadOnlyField()
    pharmacie_nom   = serializers.ReadOnlyField(source="pharmacie.nom")

    class Meta:
        model  = ConnexionLGO
        fields = [
            "id", "pharmacie", "pharmacie_nom",
            "type_lgo", "type_lgo_label",
            "version_lgo", "poste_nom", "detecte_auto",
            "statut", "statut_label",
            "derniere_sync", "nb_syncs_ok", "nb_syncs_erreur",
            "taux_succes", "derniere_erreur",
            "created_at", "updated_at",
        ]
        read_only_fields = fields


class LogSyncSerializer(serializers.ModelSerializer):
    """Log de synchronisation."""

    resultat_label      = serializers.ReadOnlyField(source="get_resultat_display")
    declenchement_label = serializers.ReadOnlyField(source="get_declenchement_display")

    class Meta:
        model  = LogSync
        fields = [
            "id", "date_sync",
            "resultat", "resultat_label",
            "declenchement", "declenchement_label",
            "produits_sync", "stocks_sync", "prix_sync",
            "duree_secondes", "message_erreur",
        ]
        read_only_fields = fields


class StatsSyncSerializer(serializers.Serializer):
    """Statistiques de synchronisation pour le dashboard admin."""

    total_connexions      = serializers.IntegerField()
    connexions_actives    = serializers.IntegerField()
    connexions_en_erreur  = serializers.IntegerField()
    syncs_aujourd_hui     = serializers.IntegerField()
    syncs_succes_7j       = serializers.IntegerField()
    syncs_echec_7j        = serializers.IntegerField()