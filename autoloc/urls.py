from django.contrib import admin
from django.conf import settings
from django.views.static import serve
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("parc.urls")),
    path("comptes/", include("comptes.urls")),
    path("reservations/", include("reservations.urls")),
    path("gestion/", include("tableau.urls")),
    path("media/<path:path>", serve, {"document_root": settings.MEDIA_ROOT}),
]

handler403 = "autoloc.views.erreur_403"
handler404 = "autoloc.views.erreur_404"
handler500 = "autoloc.views.erreur_500"
