from django.apps import AppConfig

class UsersConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.users"          # ← le nom complet avec le préfixe "apps."
    verbose_name = "Utilisateurs"