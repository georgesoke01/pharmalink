# apps/produits/admin.py
from django.contrib import admin
from django.db.models import F
from django.utils.html import format_html
from .models import Produit, Stock, Prix


@admin.register(Produit)
class ProduitAdmin(admin.ModelAdmin):

    list_display  = ("nom", "laboratoire", "categorie", "forme", "dosage", "sur_ordonnance_badge")
    list_filter   = ("categorie", "sur_ordonnance", "forme")
    search_fields = ("nom", "nom_generique", "code_cip13", "laboratoire")
    ordering      = ("nom",)

    fieldsets = (
        ("Identification",    {"fields": ("code_cip13", "nom", "nom_generique", "laboratoire", "image")}),
        ("Classification",    {"fields": ("categorie", "forme", "dosage", "sur_ordonnance")}),
        ("Informations",      {"fields": ("description", "contre_indications")}),
        ("Métadonnées",       {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )
    readonly_fields = ("created_at", "updated_at")

    @admin.display(description="Ordonnance", boolean=True)
    def sur_ordonnance_badge(self, obj):
        return obj.sur_ordonnance


@admin.register(Stock)
class StockAdmin(admin.ModelAdmin):

    list_display  = ("produit", "pharmacie", "quantite", "disponible", "seuil_alerte", "alerte_badge", "updated_at")
    list_filter   = ("disponible", "pharmacie")
    search_fields = ("produit__nom", "pharmacie__nom")
    ordering      = ("produit__nom",)

    @admin.display(description="En alerte")
    def alerte_badge(self, obj):
        if obj.est_en_alerte:
            return format_html(
                '<span style="color:white;background:#dc3545;padding:2px 6px;border-radius:4px;font-size:11px">⚠ Bas</span>'
            )
        return format_html(
            '<span style="color:white;background:#198754;padding:2px 6px;border-radius:4px;font-size:11px">OK</span>'
        )


@admin.register(Prix)
class PrixAdmin(admin.ModelAdmin):

    list_display  = ("produit", "pharmacie", "prix_fcfa_affiche", "updated_at")
    list_filter   = ("pharmacie",)
    search_fields = ("produit__nom", "pharmacie__nom")
    ordering      = ("produit__nom",)

    @admin.display(description="Prix (FCFA)")
    def prix_fcfa_affiche(self, obj):
        return f"{obj.prix_fcfa:,} FCFA"