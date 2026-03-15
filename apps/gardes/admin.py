# apps/gardes/admin.py
from django.contrib import admin
from django.utils.html import format_html
from .models import PeriodeGarde


@admin.register(PeriodeGarde)
class PeriodeGardeAdmin(admin.ModelAdmin):

    list_display   = (
        "pharmacie", "date_debut", "date_fin",
        "zone_ville", "statut_badge",
        "est_active_maintenant", "created_at",
    )
    list_filter    = ("statut", "zone_ville")
    search_fields  = ("pharmacie__nom", "zone_ville", "zone_quartier")
    ordering       = ("-date_debut",)
    date_hierarchy = "date_debut"

    fieldsets = (
        ("Pharmacie & Période", {
            "fields": ("pharmacie", "date_debut", "date_fin", "telephone_garde"),
        }),
        ("Zone géographique", {
            "fields": ("zone_ville", "zone_quartier"),
        }),
        ("Statut & Note", {
            "fields": ("statut", "note"),
        }),
        ("Métadonnées", {
            "fields": ("created_at",),
            "classes": ("collapse",),
        }),
    )
    readonly_fields = ("created_at",)

    actions = ["activer_gardes", "terminer_gardes", "annuler_gardes"]

    @admin.action(description="▶ Activer les gardes sélectionnées")
    def activer_gardes(self, request, queryset):
        count = 0
        for garde in queryset.filter(statut=PeriodeGarde.Statut.PLANIFIEE):
            garde.activer()
            count += 1
        self.message_user(request, f"{count} garde(s) activée(s).")

    @admin.action(description="■ Terminer les gardes sélectionnées")
    def terminer_gardes(self, request, queryset):
        count = 0
        for garde in queryset.filter(statut=PeriodeGarde.Statut.EN_COURS):
            garde.terminer()
            count += 1
        self.message_user(request, f"{count} garde(s) terminée(s).")

    @admin.action(description="✕ Annuler les gardes sélectionnées")
    def annuler_gardes(self, request, queryset):
        count = 0
        for garde in queryset.exclude(statut=PeriodeGarde.Statut.TERMINEE):
            garde.annuler()
            count += 1
        self.message_user(request, f"{count} garde(s) annulée(s).")

    @admin.display(description="Statut")
    def statut_badge(self, obj):
        colors = {
            "planifiee": "#0d6efd",
            "en_cours":  "#198754",
            "terminee":  "#6c757d",
            "annulee":   "#dc3545",
        }
        color = colors.get(obj.statut, "#6c757d")
        return format_html(
            '<span style="background:{};color:white;padding:2px 8px;'
            'border-radius:4px;font-size:11px">{}</span>',
            color, obj.get_statut_display(),
        )