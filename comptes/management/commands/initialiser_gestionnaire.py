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

        if not any((nom, email, mot_de_passe)):
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
                self.stdout.write(
                    self.style.SUCCESS(
                        "Le gestionnaire existe déjà ; aucun changement effectué."
                    )
                )
                return

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
