# apps/users/managers.py
from django.contrib.auth.models import UserManager
from django.db.models import Q


class CustomUserManager(UserManager):
    """Manager étendu permettant la connexion via email OU username.

    Surcharge get_by_natural_key pour que Django Auth accepte
    l'email en plus du username lors de l'authentification.
    """

    def get_by_natural_key(self, username: str):
        """Recherche un utilisateur par username OU par email.

        Args:
            username: Valeur saisie dans le champ login
                      (peut être un username ou un email).

        Returns:
            CustomUser correspondant.

        Raises:
            self.model.DoesNotExist: Si aucun utilisateur trouvé.
            self.model.MultipleObjectsReturned: Ne peut pas arriver
                car email et username sont tous les deux unique=True.
        """
        return self.get(
            Q(username__iexact=username) | Q(email__iexact=username)
        )

    def create_superuser(self, username, email=None, password=None, **extra_fields):
        """Crée un super admin avec role=super_admin et is_approved=True."""
        extra_fields.setdefault("role",        "super_admin")
        extra_fields.setdefault("is_approved", True)
        return super().create_superuser(username, email, password, **extra_fields)