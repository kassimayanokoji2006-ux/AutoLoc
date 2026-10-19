from django.urls import path

from . import views

urlpatterns = [
    path("", views.vue_accueil, name="accueil"),
    path("voitures/", views.vue_voitures, name="catalogue"),
    path("voitures/ajouter/", views.vue_ajouter_voiture, name="ajouter_voiture"),
    path("voitures/<int:pk>/", views.vue_detail_voiture, name="detail_voiture"),
    path("voitures/<int:pk>/favori/", views.bascul_fav, name="bascul_fav"),
]
