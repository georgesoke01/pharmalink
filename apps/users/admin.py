# apps/users/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from .models import CustomUser


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    """Interface d'administration pour CustomUser."""

    # ── Affichage liste ───────────────────────────────────────────────────────
    list_display  = (
        "username", "email", "nom_complet", "role_badge",
        "is_approved", "is_active", "created_at",
    )
    list_filter   = ("role", "is_approved", "is_active", "pays")
    search_fields = ("username", "email", "first_name", "last_name", "numero_licence")
    ordering      = ("-created_at",)

    # ── Détail fiche ──────────────────────────────────────────────────────────
    fieldsets = (
        ("Identifiants",  {"fields": ("username", "password")}),
        ("Informations personnelles", {
            "fields": ("first_name", "last_name", "email", "phone", "avatar"),
        }),
        ("Localisation",  {"fields": ("ville", "pays")}),
        ("Rôle & Statut", {
            "fields": ("role", "numero_licence", "is_approved", "approved_at", "approved_by"),
        }),
        ("Notifications", {"fields": ("notif_push", "notif_email")}),
        ("Permissions",   {
            "fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions"),
            "classes": ("collapse",),
        }),
        ("Dates",         {
            "fields": ("last_login", "date_joined", "created_at", "updated_at"),
            "classes": ("collapse",),
        }),
    )

    readonly_fields = ("created_at", "updated_at", "approved_at", "approved_by")

    # ── Formulaire de création ────────────────────────────────────────────────
    add_fieldsets = (
        ("Compte", {
            "classes": ("wide",),
            "fields":  ("username", "email", "role", "password1", "password2"),
        }),
    )

    # ── Actions rapides ───────────────────────────────────────────────────────
    actions = ["approuver_comptes", "rejeter_comptes"]

    @admin.action(description="✅ Approuver les comptes sélectionnés")
    def approuver_comptes(self, request, queryset):
        pharmaciens = queryset.filter(role="pharmacien")
        for user in pharmaciens:
            user.approuver(approuve_par=request.user)
        self.message_user(request, f"{pharmaciens.count()} compte(s) approuvé(s).")

    @admin.action(description="❌ Rejeter les comptes sélectionnés")
    def rejeter_comptes(self, request, queryset):
        count = queryset.filter(role="pharmacien").count()
        queryset.filter(role="pharmacien").update(
            is_approved=False, approved_at=None, approved_by=None
        )
        self.message_user(request, f"{count} compte(s) rejeté(s).")

    # ── Colonnes personnalisées ───────────────────────────────────────────────
    @admin.display(description="Rôle")
    def role_badge(self, obj):
        colors = {
            "public":      "#6c757d",
            "pharmacien":  "#0d6efd",
            "super_admin": "#dc3545",
        }
        color = colors.get(obj.role, "#6c757d")
        return format_html(
            '<span style="background:{};color:white;padding:2px 8px;'
            'border-radius:4px;font-size:11px">{}</span>',
            color,
            obj.get_role_display(),
        )