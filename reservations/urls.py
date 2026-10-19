from django.urls import path

from . import views

urlpatterns = [
    path("nouvelle/<int:voiture_id>/", views.vue_creer_reserv, name="creer_reserv"),
    path("mes-reservations/", views.vue_mes_reservations, name="mes_reservations"),
    path("gestion/", views.vue_gestion_reservations, name="gestion_reservations"),
    path("<int:pk>/statut/", views.vue_changer_statut, name="changer_statut"),
    path("<int:pk>/paiement/", views.vue_ajouter_paiement, name="ajouter_paiement"),
]
