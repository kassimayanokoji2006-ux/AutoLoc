from django.contrib import admin

from .models import Client


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ("utilisateur", "nom_complet", "telephone", "adresse")
    search_fields = (
        "utilisateur__username",
        "utilisateur__first_name",
        "utilisateur__last_name",
        "utilisateur__email",
        "telephone",
    )
    list_select_related = ("utilisateur",)

    @admin.display(description="Nom complet", ordering="utilisateur__last_name")
    def nom_complet(self, obj):
        return obj.utilisateur.get_full_name() or obj.utilisateur.username
