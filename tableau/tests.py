from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from comptes.models import Client
from parc.models import Voiture
from reservations.models import Paiem, Reserv

Utilisateur = get_user_model()


class GestionTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.personnel = Utilisateur.objects.create_user(
            username="gestionnaire",
            password="MotDePasseSolide!123",
            is_staff=True,
        )
        cls.client_utilisateur = Utilisateur.objects.create_user(
            username="client",
            password="MotDePasseSolide!123",
            first_name="Alex",
            last_name="Martin",
            email="alex@example.test",
        )
        cls.profil_client = Client.objects.create(
            utilisateur=cls.client_utilisateur,
            telephone="0600000000",
            adresse="10 rue AutoLoc",
        )
        cls.voiture = Voiture.objects.create(
            marq="Renault",
            modl="Clio",
            categ=Voiture.Categorie.CITADINE,
            immat="AA-123-AA",
            prix_j=Decimal("50.00"),
            carburant=Voiture.Carburant.ESSENCE,
            transmission=Voiture.Transmission.MANUELLE,
        )
        aujourdhui = timezone.localdate()
        cls.reserv = Reserv.objects.create(
            utilisateur=cls.client_utilisateur,
            voiture=cls.voiture,
            dat_deb=aujourdhui + timedelta(days=10),
            dat_fin=aujourdhui + timedelta(days=13),
            nb_j=3,
            mont_t=Decimal("150.00"),
        )

    def test_pages_de_gestion_refusent_les_non_autorises(self):
        url = reverse("gestion_voitures")
        reponse = self.client.get(url)
        self.assertEqual(reponse.status_code, 302)
        self.client.force_login(self.client_utilisateur)
        self.assertEqual(self.client.get(url).status_code, 403)

    def test_personnel_peut_creer_et_modifier_une_voiture(self):
        self.client.force_login(self.personnel)
        url_ajout = reverse("gestion_voiture_ajouter")
        donnees = {
            "marq": "Peugeot",
            "modl": "208",
            "categ": Voiture.Categorie.CITADINE,
            "immat": "BB-456-BB",
            "description": "Compacte",
            "prix_j": "42.50",
            "nb_places": "5",
            "carburant": Voiture.Carburant.ESSENCE,
            "transmission": Voiture.Transmission.MANUELLE,
            "active": "on",
        }
        reponse = self.client.post(url_ajout, donnees)
        self.assertEqual(reponse.status_code, 302)
        voiture = Voiture.objects.get(immat="BB-456-BB")
        self.assertRedirects(
            reponse, reverse("gestion_voiture_detail", args=[voiture.pk])
        )
        donnees["modl"] = "208 GT"
        donnees["prix_j"] = "49.00"
        reponse = self.client.post(
            reverse("gestion_voiture_modifier", args=[voiture.pk]), donnees
        )
        self.assertEqual(reponse.status_code, 302)
        voiture.refresh_from_db()
        self.assertEqual(voiture.modl, "208 GT")
        self.assertEqual(voiture.prix_j, Decimal("49.00"))

    def test_voiture_peut_etre_archivee_sans_supprimer_historique(self):
        self.client.force_login(self.personnel)
        reponse = self.client.post(
            reverse("gestion_voiture_etat", args=[self.voiture.pk])
        )
        self.assertRedirects(reponse, reverse("gestion_voitures"))
        self.voiture.refresh_from_db()
        self.assertFalse(self.voiture.active)
        self.assertTrue(Reserv.objects.filter(pk=self.reserv.pk).exists())

    def test_transition_de_reservation_autorisee(self):
        self.client.force_login(self.personnel)
        reponse = self.client.post(
            reverse("gestion_reservation_statut", args=[self.reserv.pk]),
            {"statut": Reserv.Statut.CONFIRMEE},
        )
        self.assertRedirects(
            reponse, reverse("gestion_reservation_detail", args=[self.reserv.pk])
        )
        self.reserv.refresh_from_db()
        self.assertEqual(self.reserv.statut, Reserv.Statut.CONFIRMEE)

    def test_transition_invalide_n_est_pas_appliquee(self):
        self.client.force_login(self.personnel)
        self.client.post(
            reverse("gestion_reservation_statut", args=[self.reserv.pk]),
            {"statut": Reserv.Statut.TERMINEE},
        )
        self.reserv.refresh_from_db()
        self.assertEqual(self.reserv.statut, Reserv.Statut.ATTENTE)

    def test_paiement_superieur_au_solde_est_refuse(self):
        self.client.force_login(self.personnel)
        reponse = self.client.post(
            reverse("gestion_paiement_reservation", args=[self.reserv.pk]),
            {
                "montant": "150.01",
                "date_paiem": timezone.localdate().isoformat(),
                "mode": Paiem.Mode.VIREMENT,
            },
        )
        self.assertEqual(reponse.status_code, 200)
        self.assertContains(reponse, "dépasse le solde restant")
        self.assertFalse(Paiem.objects.exists())

    def test_personnel_peut_enregistrer_un_paiement_dans_le_solde(self):
        self.client.force_login(self.personnel)
        reponse = self.client.post(
            reverse("gestion_paiement_reservation", args=[self.reserv.pk]),
            {
                "montant": "100.00",
                "date_paiem": timezone.localdate().isoformat(),
                "mode": Paiem.Mode.VIREMENT,
            },
        )
        self.assertRedirects(reponse, reverse("gestion_paiements"))
        self.assertEqual(Paiem.objects.get().montant, Decimal("100.00"))

    def test_personnel_peut_voir_le_tableau_de_bord_et_paiements(self):
        self.client.force_login(self.personnel)
        self.assertEqual(self.client.get(reverse("tableau")).status_code, 200)
        self.assertEqual(self.client.get(reverse("gestion_paiements")).status_code, 200)

    def test_pages_de_listes_et_fiches_de_gestion_sont_rendues(self):
        self.client.force_login(self.personnel)
        pages = (
            reverse("gestion_voitures"),
            reverse("gestion_voiture_ajouter"),
            reverse("gestion_voiture_detail", args=[self.voiture.pk]),
            reverse("gestion_voiture_modifier", args=[self.voiture.pk]),
            reverse("gestion_clients"),
            reverse("gestion_client_detail", args=[self.profil_client.pk]),
            reverse("gestion_reservations"),
            reverse("gestion_reservation_detail", args=[self.reserv.pk]),
            reverse("gestion_paiement_ajouter"),
            reverse("gestion_paiement_reservation", args=[self.reserv.pk]),
        )
        for url in pages:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 200)
