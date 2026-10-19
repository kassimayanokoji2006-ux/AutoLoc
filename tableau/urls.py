from django.urls import path

from . import views

urlpatterns = [
    path("", views.vue_tableau, name="tableau"),
    path("voitures/", views.vue_voitures, name="gestion_voitures"),
    path("voitures/ajouter/", views.vue_voiture_form, name="gestion_voiture_ajouter"),
    path("voitures/<int:pk>/", views.vue_voiture_detail, name="gestion_voiture_detail"),
    path("voitures/<int:pk>/modifier/", views.vue_voiture_form, name="gestion_voiture_modifier"),
    path("voitures/<int:pk>/etat/", views.vue_voiture_etat, name="gestion_voiture_etat"),
    path("clients/", views.vue_clients, name="gestion_clients"),
    path("clients/<int:pk>/", views.vue_client_detail, name="gestion_client_detail"),
    path("reservations/", views.vue_reservations, name="gestion_reservations"),
    path(
        "reservations/<int:pk>/",
        views.vue_reservation_detail,
        name="gestion_reservation_detail",
    ),
    path(
        "reservations/<int:pk>/statut/",
        views.vue_reservation_statut,
        name="gestion_reservation_statut",
    ),
    path("paiements/", views.vue_paiements, name="gestion_paiements"),
    path("paiements/ajouter/", views.vue_paiement_form, name="gestion_paiement_ajouter"),
    path(
        "reservations/<int:reserv_id>/paiement/",
        views.vue_paiement_form,
        name="gestion_paiement_reservation",
    ),
]
