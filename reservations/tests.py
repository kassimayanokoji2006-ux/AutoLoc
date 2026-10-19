from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from parc.models import Voiture

from .models import Paiem, Reserv
from .services import creer_reserv, enregistrer_paiem

Utilisateur = get_user_model()


class ReservationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.client_utilisateur = Utilisateur.objects.create_user(
            username="client", password="mot-de-passe-solide"
        )
        cls.personnel = Utilisateur.objects.create_user(
            username="gestionnaire", password="mot-de-passe-solide", is_staff=True
        )
        cls.voiture = Voiture.objects.create(
            marq="Renault",
            modl="Clio",
            categ=Voiture.Categorie.CITADINE,
            immat="AB-123-CD",
            prix_j="50.00",
            carburant=Voiture.Carburant.ESSENCE,
            transmission=Voiture.Transmission.MANUELLE,
        )

    def setUp(self):
        self.debut = timezone.localdate() + timedelta(days=10)
        self.fin = self.debut + timedelta(days=3)

    def test_calc_prix_applique_la_duree_calendaire(self):
        jours, montant = Reserv.calc_prix(self.debut, self.fin, Decimal("49.90"))
        self.assertEqual(jours, 3)
        self.assertEqual(montant, Decimal("149.70"))

    def test_calc_prix_refuse_dates_incoherentes(self):
        with self.assertRaises(ValidationError):
            Reserv.calc_prix(self.fin, self.debut, Decimal("50.00"))
        with self.assertRaises(ValidationError):
            Reserv.calc_prix(self.debut, self.debut, Decimal("50.00"))

    def test_reservation_chevauchante_est_refusee_et_periode_adjacente_acceptee(self):
        premiere = creer_reserv(
            utilisateur=self.client_utilisateur,
            voiture_id=self.voiture.pk,
            dat_deb=self.debut,
            dat_fin=self.fin,
        )
        with self.assertRaises(ValidationError):
            creer_reserv(
                utilisateur=self.client_utilisateur,
                voiture_id=self.voiture.pk,
                dat_deb=self.fin - timedelta(days=1),
                dat_fin=self.fin + timedelta(days=2),
            )
        seconde = creer_reserv(
            utilisateur=self.client_utilisateur,
            voiture_id=self.voiture.pk,
            dat_deb=self.fin,
            dat_fin=self.fin + timedelta(days=1),
        )
        self.assertEqual(premiere.statut, Reserv.Statut.ATTENTE)
        self.assertEqual(seconde.nb_j, 1)

    def test_reservation_est_protegee_et_visible_uniquement_a_son_proprietaire(self):
        reserv = creer_reserv(
            utilisateur=self.client_utilisateur,
            voiture_id=self.voiture.pk,
            dat_deb=self.debut,
            dat_fin=self.fin,
        )
        url = reverse("mes_reservations")
        self.assertEqual(self.client.get(url).status_code, 302)
        autre = Utilisateur.objects.create_user(
            username="autre", password="mot-de-passe-solide"
        )
        self.client.force_login(autre)
        reponse = self.client.get(url)
        self.assertNotContains(reponse, f"Réservation #{reserv.pk}")
        self.client.force_login(self.client_utilisateur)
        self.assertContains(self.client.get(url), "Renault Clio")

    def test_paiement_est_refuse_s_il_depasse_le_solde(self):
        reserv = creer_reserv(
            utilisateur=self.client_utilisateur,
            voiture_id=self.voiture.pk,
            dat_deb=self.debut,
            dat_fin=self.fin,
        )
        donnees = {
            "montant": Decimal("100.00"),
            "date_paiem": timezone.localdate(),
            "mode": Paiem.Mode.VIREMENT,
        }
        paiement = enregistrer_paiem(reserv_id=reserv.pk, donnees=donnees)
        self.assertEqual(paiement.montant, Decimal("100.00"))
        with self.assertRaises(ValidationError):
            enregistrer_paiem(
                reserv_id=reserv.pk,
                donnees={**donnees, "montant": Decimal("51.00")},
            )
        self.assertEqual(reserv.paiements.count(), 1)

    def test_vues_de_gestion_refusent_un_client(self):
        self.client.force_login(self.client_utilisateur)
        self.assertEqual(
            self.client.get(reverse("gestion_reservations")).status_code, 403
        )
        self.assertEqual(self.client.get(reverse("tableau")).status_code, 403)

    def test_transition_invalide_est_refusee(self):
        reserv = creer_reserv(
            utilisateur=self.client_utilisateur,
            voiture_id=self.voiture.pk,
            dat_deb=self.debut,
            dat_fin=self.fin,
        )
        self.client.force_login(self.personnel)
        reponse = self.client.post(
            reverse("changer_statut", args=[reserv.pk]),
            {"statut": Reserv.Statut.TERMINEE},
        )
        reserv.refresh_from_db()
        self.assertRedirects(reponse, reverse("gestion_reservations"))
        self.assertEqual(reserv.statut, Reserv.Statut.ATTENTE)

    def test_modele_refuse_transition_incoherente(self):
        reserv = creer_reserv(
            utilisateur=self.client_utilisateur,
            voiture_id=self.voiture.pk,
            dat_deb=self.debut,
            dat_fin=self.fin,
        )
        reserv.statut = Reserv.Statut.TERMINEE
        with self.assertRaises(ValidationError):
            reserv.save()

    def test_tableau_de_bord_est_rendu_pour_le_personnel(self):
        self.client.force_login(self.personnel)
        reponse = self.client.get(reverse("tableau"))
        self.assertEqual(reponse.status_code, 200)
        self.assertContains(reponse, "Réservations par statut")

    def test_formulaire_refuse_une_date_debut_dans_le_passe(self):
        self.client.force_login(self.client_utilisateur)
        reponse = self.client.post(
            reverse("creer_reserv", args=[self.voiture.pk]),
            {
                "dat_deb": timezone.localdate() - timedelta(days=1),
                "dat_fin": timezone.localdate() + timedelta(days=1),
            },
        )
        self.assertEqual(reponse.status_code, 200)
        self.assertContains(reponse, "ne peut pas être dans le passé")
        self.assertFalse(Reserv.objects.exists())

    def test_demande_de_reservation_exige_une_connexion(self):
        reponse = self.client.get(reverse("creer_reserv", args=[self.voiture.pk]))
        self.assertEqual(reponse.status_code, 302)
