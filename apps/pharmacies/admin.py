# apps/pharmacies/admin.py
from django.contrib import admin
from django.utils.html import format_html
from .models import Pharmacie


@admin.register(Pharmacie)
class PharmacieAdmin(admin.ModelAdmin):
    """Interface d'administration pour les pharmacies."""

    # ── Affichage liste ───────────────────────────────────────────────────────
    list_display  = (
        "nom", "ville", "pharmacien", "statut_badge",
        "est_ouverte", "est_de_garde", "created_at",
    )
    list_filter   = ("statut", "ville", "est_ouverte", "est_de_garde")
    search_fields = ("nom", "adresse", "ville", "numero_agrement", "pharmacien__username")
    ordering      = ("-created_at",)
    date_hierarchy = "created_at"

    # ── Détail fiche ──────────────────────────────────────────────────────────
    fieldsets = (
        ("Informations générales", {
            "fields": ("pharmacien", "nom", "numero_agrement", "siret", "description", "logo"),
        }),
        ("Services", {
            "fields": ("services",),
        }),
        ("Coordonnées", {
            "fields": ("adresse", "ville", "code_postal", "telephone", "email", "site_web"),
        }),
        ("Géolocalisation", {
            "fields": ("latitude", "longitude", "localisation"),
            "classes": ("collapse",),
        }),
        ("Statut", {
            "fields": ("statut", "est_ouverte", "est_de_garde"),
        }),
        ("Métadonnées", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",),
        }),
    )
    readonly_fields = ("created_at", "updated_at", "localisation")

    # ── Actions rapides ───────────────────────────────────────────────────────
    actions = ["activer_pharmacies", "suspendre_pharmacies"]

    @admin.action(description="✅ Activer les pharmacies sélectionnées")
    def activer_pharmacies(self, request, queryset):
        for pharmacie in queryset:
            pharmacie.activer(request.user)
        self.message_user(request, f"{queryset.count()} pharmacie(s) activée(s).")

    @admin.action(description="🚫 Suspendre les pharmacies sélectionnées")
    def suspendre_pharmacies(self, request, queryset):
        queryset.update(statut=Pharmacie.Statut.SUSPENDUE)
        self.message_user(request, f"{queryset.count()} pharmacie(s) suspendue(s).")

    # ── Badge statut ──────────────────────────────────────────────────────────
    @admin.display(description="Statut")
    def statut_badge(self, obj):
        colors = {
            "en_attente": "#fd7e14",
            "active":     "#198754",
            "suspendue":  "#dc3545",
        }
        color = colors.get(obj.statut, "#6c757d")
        return format_html(
            '<span style="background:{};color:white;padding:2px 8px;'
            'border-radius:4px;font-size:11px">{}</span>',
            color,
            obj.get_statut_display(),
        )