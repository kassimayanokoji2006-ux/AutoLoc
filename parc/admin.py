from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import Favori, Voiture

admin.site.site_header = _("Administration AutoLoc")
admin.site.site_title = _("Gestion AutoLoc")
admin.site.index_title = _("Gestion du parc et des locations")


@admin.register(Voiture)
class VoitureAdmin(admin.ModelAdmin):
    list_display = ("marq", "modl", "immat", "categ", "prix_j", "active")
    list_filter = ("active", "categ", "carburant", "transmission")
    search_fields = ("marq", "modl", "immat")
    list_editable = ("active",)
    ordering = ("marq", "modl")


admin.site.register(Favori)
