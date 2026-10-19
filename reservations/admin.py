from django.contrib import admin

from .models import Paiem, Reserv


class PaiemInline(admin.TabularInline):
    model = Paiem
    extra = 0


@admin.register(Reserv)
class ReservAdmin(admin.ModelAdmin):
    list_display = (
        "id", "utilisateur", "voiture", "dat_deb", "dat_fin", "statut", "mont_t"
    )
    list_filter = ("statut", "dat_deb", "dat_fin")
    search_fields = ("utilisateur__username", "utilisateur__email", "voiture__marq", "voiture__modl")
    list_select_related = ("utilisateur", "voiture")
    inlines = (PaiemInline,)


@admin.register(Paiem)
class PaiemAdmin(admin.ModelAdmin):
    list_display = ("reserv", "montant", "date_paiem", "mode", "statut")
    list_filter = ("mode", "statut", "date_paiem")
    search_fields = ("reserv__utilisateur__username", "reserv__voiture__marq")
    list_select_related = ("reserv", "reserv__utilisateur", "reserv__voiture")
