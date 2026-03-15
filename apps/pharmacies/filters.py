# apps/pharmacies/filters.py
import django_filters
from django.conf import settings
from django.db.models import QuerySet

_USE_POSTGIS = getattr(settings, "USE_POSTGIS", False)

from .models import Pharmacie

# Services disponibles — utilisés pour validation côté filtre
SERVICES_DISPONIBLES = [
    "livraison",
    "urgences",
    "vaccins",
    "bebe",
    "dermatologie",
    "veterinaire",
    "garde_nuit",
    "ordonnance_en_ligne",
]


class PharmacieFilter(django_filters.FilterSet):
    """Filtres avancés pour la liste des pharmacies.

    Paramètres supportés :
        ?ville=Cotonou
        ?statut=active
        ?est_ouverte=true
        ?est_de_garde=true
        ?service=livraison
        ?lat=6.3703&lng=2.3912&rayon=5      → dans un rayon de 5km
        ?search=pharmacie+centrale           → recherche textuelle
    """

    # ── Filtres simples ───────────────────────────────────────────────────────
    ville       = django_filters.CharFilter(lookup_expr="icontains")
    statut      = django_filters.ChoiceFilter(choices=Pharmacie.Statut.choices)
    est_ouverte = django_filters.BooleanFilter()
    est_de_garde = django_filters.BooleanFilter()

    # ── Recherche textuelle (nom, ville, adresse) ─────────────────────────────
    search = django_filters.CharFilter(method="filter_search", label="Recherche")

    # ── Filtres géographiques ─────────────────────────────────────────────────
    # Utilisés ensemble : ?lat=6.37&lng=2.39&rayon=5
    lat   = django_filters.NumberFilter(method="filter_geo", label="Latitude")
    lng   = django_filters.NumberFilter(method="filter_geo", label="Longitude")
    rayon = django_filters.NumberFilter(method="filter_geo", label="Rayon (km)")

    # ── Filtre service ────────────────────────────────────────────────────────
    # ?service=livraison → pharmacies proposant ce service
    service = django_filters.CharFilter(method="filter_service", label="Service")

    class Meta:
        model  = Pharmacie
        fields = ["ville", "statut", "est_ouverte", "est_de_garde"]

    def filter_search(self, queryset: QuerySet, name: str, value: str) -> QuerySet:
        """Recherche dans nom, adresse et ville."""
        return queryset.filter(
            nom__icontains=value
        ) | queryset.filter(
            adresse__icontains=value
        ) | queryset.filter(
            ville__icontains=value
        )

    def filter_geo(self, queryset: QuerySet, name: str, value) -> QuerySet:
        """Filtre par rayon géographique.

        Nécessite lat + lng + rayon dans les paramètres.
        En dev (SQLite/SpatiaLite) : filtre approximatif par bounding box.
        En prod (PostGIS) : filtre précis en mètres via geography=True.
        """
        params = self.request.query_params if self.request else {}
        lat   = params.get("lat")
        lng   = params.get("lng")
        rayon = params.get("rayon", 5)    # défaut : 5 km

        if not (lat and lng):
            return queryset

        try:
            lat   = float(lat)
            lng   = float(lng)
            rayon = float(rayon)
        except (TypeError, ValueError):
            return queryset

        # PostGIS disponible → requête spatiale précise
        if _USE_POSTGIS:
            from django.contrib.gis.geos import Point
            from django.contrib.gis.measure import Distance
            point = Point(lng, lat, srid=4326)
            return queryset.filter(
                localisation__distance_lte=(point, Distance(km=rayon))
            )

        # Dev SQLite → bounding box approximative (~111 km par degré)
        delta = rayon / 111.0
        return queryset.filter(
            latitude__range=(lat - delta, lat + delta),
            longitude__range=(lng - delta, lng + delta),
        )

    def filter_service(self, queryset: QuerySet, name: str, value: str) -> QuerySet:
        """Filtre les pharmacies proposant un service donné.
        Le champ services est un JSONField contenant une liste de chaînes.
        """
        return queryset.filter(services__contains=value)