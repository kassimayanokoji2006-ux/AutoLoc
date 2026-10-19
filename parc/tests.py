from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from reservations.models import Reserv
from .models import Favori, Voiture

Utilisateur = get_user_model()


class CatalogueTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.voiture = Voiture.objects.create(
            marq="Renault",
            modl="Clio",
            categ=Voiture.Categorie.CITADINE,
            immat="AA-123-AA",
            prix_j="45.00",
            carburant=Voiture.Carburant.ESSENCE,
            transmission=Voiture.Transmission.MANUELLE,
        )
        cls.autre = Voiture.objects.create(
            marq="Tesla",
            modl="Model 3",
            categ=Voiture.Categorie.BERLINE,
            immat="BB-456-BB",
            prix_j="90.00",
            carburant=Voiture.Carburant.ELECTRIQUE,
            transmission=Voiture.Transmission.AUTOMATIQUE,
        )
        cls.archivee = Voiture.objects.create(
            marq="Peugeot",
            modl="208",
            categ=Voiture.Categorie.CITADINE,
            immat="CC-789-CC",
            prix_j="30.00",
            carburant=Voiture.Carburant.DIESEL,
            transmission=Voiture.Transmission.MANUELLE,
            active=False,
        )
        cls.utilisateur = Utilisateur.objects.create_user(
            username="cliente", password="mot-de-passe-solide"
        )

    def test_catalogue_affiche_uniquement_voitures_actives(self):
        reponse = self.client.get(reverse("catalogue"))
        self.assertEqual(reponse.status_code, 200)
        self.assertContains(reponse, "Renault Clio")
        self.assertContains(reponse, "Tesla Model 3")
        self.assertNotContains(reponse, "Peugeot 208")

    def test_recherche_marque_categorie_et_carburant(self):
        reponse = self.client.get(
            reverse("catalogue"),
            {"q": "renault", "categ": "citadine", "carburant": "essence"},
        )
        self.assertContains(reponse, "Renault Clio")
        self.assertNotContains(reponse, "Tesla Model 3")

    def test_filtre_prix_et_tri(self):
        reponse = self.client.get(
            reverse("catalogue"),
            {"prix_min": "40", "prix_max": "50", "tri": "prix_decroissant"},
        )
        self.assertContains(reponse, "Renault Clio")
        self.assertNotContains(reponse, "Tesla Model 3")

    def test_parametres_invalides_sont_ignores(self):
        reponse = self.client.get(
            reverse("catalogue"),
            {"tri": "injection", "categ": "inconnue", "prix_min": "pas-un-prix"},
        )
        self.assertEqual(reponse.status_code, 200)
        self.assertEqual(reponse.context["nombre_voitures"], 2)

    def test_filtre_disponibilite_exclut_les_locations_en_cours(self):
        aujourd_hui = timezone.localdate()
        Reserv.objects.create(
            utilisateur=self.utilisateur,
            voiture=self.voiture,
            dat_deb=aujourd_hui,
            dat_fin=aujourd_hui + timedelta(days=2),
            nb_j=2,
            mont_t="90.00",
            statut=Reserv.Statut.CONFIRMEE,
        )
        reponse = self.client.get(reverse("catalogue"), {"disponibles": "1"})
        self.assertEqual(reponse.context["nombre_voitures"], 1)
        self.assertContains(reponse, "Tesla Model 3")

    def test_favori_requiert_authentification_et_peut_etre_bascule(self):
        url = reverse("bascul_fav", args=[self.voiture.pk])
        reponse = self.client.post(url)
        self.assertEqual(reponse.status_code, 302)
        self.client.force_login(self.utilisateur)
        reponse = self.client.post(url)
        self.assertEqual(reponse.status_code, 200)
        self.assertTrue(reponse.json()["favori"])
        self.assertTrue(
            Favori.objects.filter(utilisateur=self.utilisateur, voiture=self.voiture).exists()
        )
        reponse = self.client.post(url)
        self.assertFalse(reponse.json()["favori"])
        self.assertFalse(Favori.objects.exists())

    def test_inscription_cree_un_compte_et_un_profil_client(self):
        reponse = self.client.post(
            reverse("inscription"),
            {
                "username": "nouvelle",
                "prenom": "Ada",
                "nom": "Lovelace",
                "email": "ada@example.test",
                "telephone": "0600000000",
                "password1": "UnMotDePasseTresFort!48",
                "password2": "UnMotDePasseTresFort!48",
            },
        )
        self.assertRedirects(reponse, reverse("accueil"))
        utilisateur = Utilisateur.objects.get(username="nouvelle")
        self.assertEqual(utilisateur.profil.telephone, "0600000000")
