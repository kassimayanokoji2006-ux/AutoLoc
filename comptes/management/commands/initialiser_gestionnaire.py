import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction


class Command(BaseCommand):
    help = "Crée le compte personnel initial depuis des variables d'environnement."

    def handle(self, *args, **options):
        nom = os.environ.get("AUTOLOC_ADMIN_USERNAME", "").strip()
        email = os.environ.get("AUTOLOC_ADMIN_EMAIL", "").strip()
        mot_de_passe = os.environ.get("AUTOLOC_ADMIN_PASSWORD", "")
        reinitialiser = os.environ.get("AUTOLOC_ADMIN_RESET_PASSWORD", "").strip().lower()

        valeurs_vraies = {"1", "true"}
        valeurs_fausses = {"", "0", "false"}
        if reinitialiser not in valeurs_vraies | valeurs_fausses:
            raise CommandError(
                "AUTOLOC_ADMIN_RESET_PASSWORD doit valoir true, false, 1 ou 0."
            )
        reinitialisation_active = reinitialiser in valeurs_vraies

        if not any((nom, email, mot_de_passe)) and not reinitialisation_active:
            self.stdout.write(
                "Création du gestionnaire ignorée : variables AUTOLOC_ADMIN_* absentes."
            )
            return
        if not nom:
            raise CommandError(
                "AUTOLOC_ADMIN_USERNAME est requis pour initialiser le gestionnaire."
            )

        Utilisateur = get_user_model()
        with transaction.atomic():
            utilisateur = Utilisateur.objects.filter(username=nom).first()
            if utilisateur:
                if not utilisateur.is_superuser:
                    raise CommandError(
                        "Le nom AUTOLOC_ADMIN_USERNAME existe déjà pour un compte "
                        "qui n'est pas superutilisateur. Choisissez un autre nom."
                    )
                if reinitialisation_active:
                    if not mot_de_passe:
                        raise CommandError(
                            "AUTOLOC_ADMIN_PASSWORD est requis pour réinitialiser "
                            "le mot de passe."
                        )
                    utilisateur.set_password(mot_de_passe)
                    utilisateur.save(update_fields=["password"])
                    self.stdout.write(
                        self.style.SUCCESS(
                            "Le mot de passe du gestionnaire a été réinitialisé."
                        )
                    )
                    return
                self.stdout.write(
                    self.style.SUCCESS(
                        "Le gestionnaire existe déjà ; aucun changement effectué."
                    )
                )
                return

            if reinitialisation_active:
                raise CommandError(
                    "La réinitialisation est activée, mais aucun superutilisateur "
                    "avec AUTOLOC_ADMIN_USERNAME n'existe."
                )

            if not email or not mot_de_passe:
                raise CommandError(
                    "Pour créer un nouveau compte, définissez "
                    "AUTOLOC_ADMIN_EMAIL et AUTOLOC_ADMIN_PASSWORD dans "
                    "l'environnement Render."
                )

            Utilisateur.objects.create_superuser(
                username=nom,
                email=email,
                password=mot_de_passe,
            )

        self.stdout.write(
            self.style.SUCCESS("Le compte gestionnaire initial a été créé.")
        )
