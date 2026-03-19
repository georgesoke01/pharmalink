# tests/factories.py
"""
Factories Factory Boy — données de test réutilisables pour toutes les apps.

Chaque factory génère des objets Django valides avec des données cohérentes.
Utilisées dans conftest.py et directement dans les tests.

Usage :
    # Créer un objet simple
    user = UserPublicFactory()

    # Surcharger des champs
    pharmacie = PharmacieActiveFactory(ville="Cotonou", nom="Pharmacie Test")

    # Créer plusieurs objets
    produits = ProduitFactory.create_batch(10)

    # Build sans sauvegarder en DB
    user = UserPublicFactory.build()
"""
import factory
from factory.django import DjangoModelFactory
from django.utils import timezone
from datetime import timedelta


# ─────────────────────────────────────────────────────────────────────────────
# USERS
# ─────────────────────────────────────────────────────────────────────────────

class UserPublicFactory(DjangoModelFactory):
    """Utilisateur public standard (app mobile)."""

    class Meta:
        model = "users.CustomUser"
        django_get_or_create = ("username",)

    username    = factory.Sequence(lambda n: f"user_{n}")
    email       = factory.LazyAttribute(lambda o: f"{o.username}@test.com")
    first_name  = factory.Faker("first_name", locale="fr_FR")
    last_name   = factory.Faker("last_name", locale="fr_FR")
    role        = "public"
    is_approved = False
    is_active   = True
    password    = factory.PostGenerationMethodCall("set_password", "testpass123!")


class UserPharmacienFactory(DjangoModelFactory):
    """Pharmacien en attente d'approbation."""

    class Meta:
        model = "users.CustomUser"
        django_get_or_create = ("username",)

    username       = factory.Sequence(lambda n: f"pharmacien_{n}")
    email          = factory.LazyAttribute(lambda o: f"{o.username}@pharmacie.bj")
    first_name     = factory.Faker("first_name", locale="fr_FR")
    last_name      = factory.Faker("last_name", locale="fr_FR")
    role           = "pharmacien"
    is_approved    = False
    is_active      = True
    numero_licence = factory.Sequence(lambda n: f"LIC-BJ-{n:04d}")
    ville          = "Cotonou"
    pays           = "Bénin"
    password       = factory.PostGenerationMethodCall("set_password", "testpass123!")


class UserPharmacienApprouveFactory(UserPharmacienFactory):
    """Pharmacien approuvé — accès complet."""

    username    = factory.Sequence(lambda n: f"pharmacien_ok_{n}")
    is_approved = True
    approved_at = factory.LazyFunction(timezone.now)

    @factory.post_generation
    def set_approved_by(self, create, extracted, **kwargs):
        if create and not self.approved_by:
            admin = SuperAdminFactory()
            self.approved_by = admin
            self.save(update_fields=["approved_by"])


class SuperAdminFactory(DjangoModelFactory):
    """Super administrateur de la plateforme."""

    class Meta:
        model = "users.CustomUser"
        django_get_or_create = ("username",)

    username    = factory.Sequence(lambda n: f"admin_{n}")
    email       = factory.LazyAttribute(lambda o: f"{o.username}@pharmalink.bj")
    role        = "super_admin"
    is_approved = True
    is_active   = True
    is_staff    = True
    password    = factory.PostGenerationMethodCall("set_password", "adminpass123!")


# ─────────────────────────────────────────────────────────────────────────────
# PHARMACIES
# ─────────────────────────────────────────────────────────────────────────────

class PharmacieFactory(DjangoModelFactory):
    """Pharmacie en attente d'approbation."""

    class Meta:
        model = "pharmacies.Pharmacie"

    pharmacien      = factory.SubFactory(UserPharmacienApprouveFactory)
    nom             = factory.Sequence(lambda n: f"Pharmacie Test {n}")
    numero_agrement = factory.Sequence(lambda n: f"AGR-BJ-{n:04d}")
    adresse         = factory.Faker("street_address", locale="fr_FR")
    ville           = factory.Iterator(["Cotonou", "Porto-Novo", "Parakou", "Abomey-Calavi"])
    code_postal     = "00229"
    telephone       = factory.Sequence(lambda n: f"+22997{n:06d}")
    email           = factory.LazyAttribute(lambda o: f"contact@{o.nom.lower().replace(' ', '')}.bj")
    latitude        = factory.Faker("latitude")
    longitude       = factory.Faker("longitude")
    statut          = "en_attente"
    services        = factory.LazyFunction(lambda: ["livraison", "vaccins"])


class PharmacieActiveFactory(PharmacieFactory):
    """Pharmacie active (approuvée)."""
    statut = "active"


class PharmacieSuspendueFactory(PharmacieFactory):
    """Pharmacie suspendue."""
    statut = "suspendue"


# ─────────────────────────────────────────────────────────────────────────────
# PRODUITS
# ─────────────────────────────────────────────────────────────────────────────

class ProduitFactory(DjangoModelFactory):
    """Médicament standard."""

    class Meta:
        model = "produits.Produit"

    code_cip13     = factory.Sequence(lambda n: f"{n:013d}")
    nom            = factory.Sequence(lambda n: f"Paracétamol {n}mg")
    nom_generique  = "Paracétamol"
    laboratoire    = factory.Iterator(["Sanofi", "Pfizer", "Roche", "GSK"])
    categorie      = "medicament"
    forme          = factory.Iterator(["comprimes", "sirop", "injection", "gelules"])
    dosage         = factory.Iterator(["500mg", "1000mg", "250mg/5ml", "250mg"])
    sur_ordonnance = False


class ProduitOrdonanceFactory(ProduitFactory):
    """Médicament sur ordonnance."""
    nom            = factory.Sequence(lambda n: f"Amoxicilline {n}mg")
    sur_ordonnance = True
    contre_indications = "Allergie aux pénicillines."


class ProduitParapharmacieFactory(ProduitFactory):
    """Produit de parapharmacie."""
    nom       = factory.Sequence(lambda n: f"Crème hydratante {n}")
    categorie = "parapharmacie"
    forme     = "creme"


class StockFactory(DjangoModelFactory):
    """Stock d'un produit dans une pharmacie."""

    class Meta:
        model = "produits.Stock"
        django_get_or_create = ("pharmacie", "produit")

    pharmacie    = factory.SubFactory(PharmacieActiveFactory)
    produit      = factory.SubFactory(ProduitFactory)
    quantite     = factory.Faker("random_int", min=0, max=500)
    disponible   = True
    seuil_alerte = 10


class StockVideFactory(StockFactory):
    """Stock épuisé."""
    quantite   = 0
    disponible = False


class StockEnAlerteFactory(StockFactory):
    """Stock sous le seuil d'alerte."""
    quantite     = 5
    seuil_alerte = 10
    disponible   = True


class PrixFactory(DjangoModelFactory):
    """Prix d'un produit dans une pharmacie."""

    class Meta:
        model = "produits.Prix"
        django_get_or_create = ("pharmacie", "produit")

    pharmacie = factory.SubFactory(PharmacieActiveFactory)
    produit   = factory.SubFactory(ProduitFactory)
    prix_fcfa = factory.Faker("random_int", min=500, max=50000)


# ─────────────────────────────────────────────────────────────────────────────
# HORAIRES
# ─────────────────────────────────────────────────────────────────────────────

class HoraireSemaineFactory(DjangoModelFactory):
    """Horaire hebdomadaire — lundi ouvert 08h-20h."""

    class Meta:
        model = "horaires.HoraireSemaine"
        django_get_or_create = ("pharmacie", "jour")

    pharmacie       = factory.SubFactory(PharmacieActiveFactory)
    jour            = factory.Iterator([0, 1, 2, 3, 4, 5, 6])
    heure_ouverture = factory.LazyFunction(lambda: __import__("datetime").time(8, 0))
    heure_fermeture = factory.LazyFunction(lambda: __import__("datetime").time(20, 0))
    est_ferme       = False


class HoraireFermeFactory(HoraireSemaineFactory):
    """Horaire — journée fermée (ex: dimanche)."""
    jour            = 6
    heure_ouverture = None
    heure_fermeture = None
    est_ferme       = True


class HoraireAvecPauseFactory(HoraireSemaineFactory):
    """Horaire avec pause midi."""
    pause_debut = factory.LazyFunction(lambda: __import__("datetime").time(12, 30))
    pause_fin   = factory.LazyFunction(lambda: __import__("datetime").time(14, 30))


class HoraireExceptionnelFactory(DjangoModelFactory):
    """Horaire exceptionnel — fermeture un jour donné."""

    class Meta:
        model = "horaires.HoraireExceptionnel"
        django_get_or_create = ("pharmacie", "date")

    pharmacie = factory.SubFactory(PharmacieActiveFactory)
    date      = factory.LazyFunction(
        lambda: (timezone.now() + timedelta(days=3)).date()
    )
    est_ferme = True
    motif     = "Fête nationale"


class HoraireExceptionnelOuvertFactory(HoraireExceptionnelFactory):
    """Horaire exceptionnel — ouverture un jour habituellement fermé."""
    est_ferme       = False
    heure_ouverture = factory.LazyFunction(lambda: __import__("datetime").time(9, 0))
    heure_fermeture = factory.LazyFunction(lambda: __import__("datetime").time(13, 0))


# ─────────────────────────────────────────────────────────────────────────────
# GARDES
# ─────────────────────────────────────────────────────────────────────────────

class PeriodeGardeFactory(DjangoModelFactory):
    """Garde planifiée dans le futur."""

    class Meta:
        model = "gardes.PeriodeGarde"

    pharmacie       = factory.SubFactory(PharmacieActiveFactory)
    date_debut      = factory.LazyFunction(lambda: timezone.now() + timedelta(hours=2))
    date_fin        = factory.LazyFunction(lambda: timezone.now() + timedelta(hours=14))
    telephone_garde = factory.Sequence(lambda n: f"+22997{n:06d}")
    zone_ville      = "Cotonou"
    zone_quartier   = "Cadjehoun"
    statut          = "planifiee"
    note            = "Garde de nuit"


class PeriodeGardeEnCoursFactory(PeriodeGardeFactory):
    """Garde actuellement en cours."""
    date_debut = factory.LazyFunction(lambda: timezone.now() - timedelta(hours=2))
    date_fin   = factory.LazyFunction(lambda: timezone.now() + timedelta(hours=6))
    statut     = "en_cours"


class PeriodeGardeTermineeFactory(PeriodeGardeFactory):
    """Garde passée terminée."""
    date_debut = factory.LazyFunction(lambda: timezone.now() - timedelta(days=3))
    date_fin   = factory.LazyFunction(lambda: timezone.now() - timedelta(days=2))
    statut     = "terminee"


# ─────────────────────────────────────────────────────────────────────────────
# CONNECTEURS LGO
# ─────────────────────────────────────────────────────────────────────────────

class ConnexionLGOFactory(DjangoModelFactory):
    """Connexion LGO active — Pharmagest SQLite."""

    class Meta:
        model = "connecteurs_lgo.ConnexionLGO"
        django_get_or_create = ("pharmacie",)

    pharmacie   = factory.SubFactory(PharmacieActiveFactory)
    type_lgo    = "pharmagest"
    version_lgo = "8.2.1"
    poste_nom   = "PC-PHARMACIE-01"
    config      = factory.LazyFunction(lambda: {
        "db_path":                 "C:\\Pharmagest\\Data\\pharma.db",
        "db_type":                 "sqlite",
        "detecte_automatiquement": True,
        "chemin_installation":     "C:\\Pharmagest\\",
    })
    detecte_auto = True
    statut       = "active"
    nb_syncs_ok  = 5


class ConnexionLGOErreurFactory(ConnexionLGOFactory):
    """Connexion LGO en erreur."""
    statut          = "erreur"
    nb_syncs_erreur = 3
    derniere_erreur = "Fichier DB introuvable : C:\\Pharmagest\\Data\\pharma.db"


class ConnexionWinpharmaFactory(ConnexionLGOFactory):
    """Connexion LGO Winpharma MySQL."""
    type_lgo = "winpharma"
    config   = factory.LazyFunction(lambda: {
        "db_type":  "mysql",
        "db_host":  "127.0.0.1",
        "db_port":  3306,
        "db_name":  "winpharma",
        "db_user":  "pharmalink_ro",
        "detecte_automatiquement": True,
    })