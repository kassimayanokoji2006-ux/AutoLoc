import os
from io import StringIO
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase

Utilisateur = get_user_model()


class InitialiserGestionnaireTests(TestCase):
    def setUp(self):
        self.environnement = patch.dict(os.environ, {}, clear=False)
        self.environnement.start()
        for cle in (
            "AUTOLOC_ADMIN_USERNAME",
            "AUTOLOC_ADMIN_EMAIL",
            "AUTOLOC_ADMIN_PASSWORD",
            "AUTOLOC_ADMIN_RESET_PASSWORD",
        ):
            os.environ.pop(cle, None)
        self.addCleanup(self.environnement.stop)

    def configurer_identifiants(self):
        os.environ.update(
            {
                "AUTOLOC_ADMIN_USERNAME": "gestion",
                "AUTOLOC_ADMIN_EMAIL": "gestion@example.test",
                "AUTOLOC_ADMIN_PASSWORD": "MotDePasseLong!EtUnique2026",
            }
        )

    def test_commande_sans_variables_ne_cree_pas_de_compte(self):
        call_command("initialiser_gestionnaire", stdout=StringIO())
        self.assertFalse(Utilisateur.objects.exists())

    def test_commande_ignore_le_drapeau_desactive_sans_identifiants(self):
        os.environ["AUTOLOC_ADMIN_RESET_PASSWORD"] = "false"
        call_command("initialiser_gestionnaire", stdout=StringIO())
        self.assertFalse(Utilisateur.objects.exists())

    def test_commande_cree_un_superutilisateur_et_reste_idempotente(self):
        self.configurer_identifiants()
        call_command("initialiser_gestionnaire", stdout=StringIO())
        utilisateur = Utilisateur.objects.get(username="gestion")
        self.assertTrue(utilisateur.is_superuser)
        self.assertTrue(utilisateur.check_password(os.environ["AUTOLOC_ADMIN_PASSWORD"]))

        os.environ.pop("AUTOLOC_ADMIN_PASSWORD")
        call_command("initialiser_gestionnaire", stdout=StringIO())
        self.assertTrue(Utilisateur.objects.filter(username="gestion").exists())

        os.environ["AUTOLOC_ADMIN_PASSWORD"] = "AutreMotDePasse!QuiNeDoitPasRemplacer"
        call_command("initialiser_gestionnaire", stdout=StringIO())
        utilisateur.refresh_from_db()
        self.assertTrue(utilisateur.check_password("MotDePasseLong!EtUnique2026"))
        self.assertFalse(
            utilisateur.check_password("AutreMotDePasse!QuiNeDoitPasRemplacer")
        )

    def test_commande_refuse_des_variables_partielles(self):
        os.environ["AUTOLOC_ADMIN_USERNAME"] = "gestion"
        with self.assertRaises(CommandError):
            call_command("initialiser_gestionnaire", stdout=StringIO())

    def test_commande_ne_promouvoit_pas_un_compte_ordinaire_existant(self):
        Utilisateur.objects.create_user(
            username="gestion",
            email="client@example.test",
            password="MotDePasseLong!EtUnique2026",
        )
        self.configurer_identifiants()
        with self.assertRaises(CommandError):
            call_command("initialiser_gestionnaire", stdout=StringIO())
        self.assertFalse(Utilisateur.objects.get(username="gestion").is_superuser)

    def test_commande_reinitialise_seulement_si_explicitement_activee(self):
        utilisateur = Utilisateur.objects.create_superuser(
            username="gestion",
            email="gestion@example.test",
            password="AncienMotDePasse!2026",
        )
        self.configurer_identifiants()

        call_command("initialiser_gestionnaire", stdout=StringIO())
        utilisateur.refresh_from_db()
        self.assertTrue(utilisateur.check_password("AncienMotDePasse!2026"))

        os.environ["AUTOLOC_ADMIN_RESET_PASSWORD"] = "true"
        call_command("initialiser_gestionnaire", stdout=StringIO())
        utilisateur.refresh_from_db()
        self.assertTrue(utilisateur.check_password("MotDePasseLong!EtUnique2026"))
        self.assertFalse(utilisateur.check_password("AncienMotDePasse!2026"))

    def test_reinitialisation_refuse_un_compte_absent(self):
        self.configurer_identifiants()
        os.environ["AUTOLOC_ADMIN_RESET_PASSWORD"] = "true"
        with self.assertRaises(CommandError):
            call_command("initialiser_gestionnaire", stdout=StringIO())

    def test_reinitialisation_refuse_un_mot_de_passe_absent(self):
        Utilisateur.objects.create_superuser(
            username="gestion",
            email="gestion@example.test",
            password="AncienMotDePasse!2026",
        )
        os.environ["AUTOLOC_ADMIN_USERNAME"] = "gestion"
        os.environ["AUTOLOC_ADMIN_RESET_PASSWORD"] = "true"
        with self.assertRaises(CommandError):
            call_command("initialiser_gestionnaire", stdout=StringIO())
