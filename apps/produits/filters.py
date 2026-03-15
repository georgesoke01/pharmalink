# apps/produits/filters.py
import django_filters
from .models import Produit, Stock


class ProduitFilter(django_filters.FilterSet):
    """Filtres avancés pour la liste des produits.

    Paramètres supportés :
        ?search=paracetamol          → nom, nom_generique, code_cip13, laboratoire
        ?categorie=medicament
        ?sur_ordonnance=true
        ?forme=comprimes
        ?laboratoire=sanofi
        ?pharmacie_id=3              → produits disponibles dans cette pharmacie
        ?disponible=true             → produits en stock dans au moins une pharmacie
    """

    # ── Recherche textuelle ───────────────────────────────────────────────────
    search = django_filters.CharFilter(
        method="filter_search",
        label="Recherche (nom, code, laboratoire)",
    )

    # ── Filtres simples ───────────────────────────────────────────────────────
    categorie      = django_filters.ChoiceFilter(choices=Produit.Categorie.choices)
    sur_ordonnance = django_filters.BooleanFilter()
    forme          = django_filters.ChoiceFilter(choices=Produit.Forme.choices)
    laboratoire    = django_filters.CharFilter(lookup_expr="icontains")

    # ── Filtres liés au stock ─────────────────────────────────────────────────
    # ?pharmacie_id=3 → produits présents dans cette pharmacie
    pharmacie_id = django_filters.NumberFilter(
        method="filter_par_pharmacie",
        label="ID Pharmacie",
    )
    # ?disponible=true → produits en stock dans au moins une pharmacie
    disponible = django_filters.BooleanFilter(
        method="filter_disponible",
        label="Disponible en stock",
    )

    class Meta:
        model  = Produit
        fields = ["categorie", "sur_ordonnance", "forme", "laboratoire"]

    def filter_search(self, queryset, name, value):
        """Recherche sur nom, nom_generique, code_cip13 et laboratoire."""
        return (
            queryset.filter(nom__icontains=value)
            | queryset.filter(nom_generique__icontains=value)
            | queryset.filter(code_cip13__icontains=value)
            | queryset.filter(laboratoire__icontains=value)
        ).distinct()

    def filter_par_pharmacie(self, queryset, name, value):
        """Filtre les produits disponibles dans une pharmacie donnée."""
        return queryset.filter(
            stocks__pharmacie_id=value,
            stocks__disponible=True,
        ).distinct()

    def filter_disponible(self, queryset, name, value):
        """Filtre les produits disponibles dans au moins une pharmacie."""
        if value:
            return queryset.filter(stocks__disponible=True).distinct()
        return queryset.filter(stocks__disponible=False).distinct()


class StockFilter(django_filters.FilterSet):
    """Filtres pour les stocks — utilisé par le pharmacien.

    Paramètres :
        ?disponible=true
        ?en_alerte=true    → stocks sous le seuil d'alerte
        ?search=doliprane
    """

    disponible = django_filters.BooleanFilter()
    search     = django_filters.CharFilter(
        field_name="produit__nom",
        lookup_expr="icontains",
        label="Nom du produit",
    )
    en_alerte  = django_filters.BooleanFilter(
        method="filter_en_alerte",
        label="Stock en alerte",
    )

    class Meta:
        model  = Stock
        fields = ["disponible"]

    def filter_en_alerte(self, queryset, name, value):
        """Stocks dont la quantité est <= seuil_alerte (et seuil > 0)."""
        if value:
            from django.db.models import F
            return queryset.filter(
                seuil_alerte__gt=0,
                quantite__lte=F("seuil_alerte"),
            )
        return queryset