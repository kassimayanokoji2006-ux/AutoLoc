from django.conf import settings
from django.db import models


class Client(models.Model):
    utilisateur = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profil"
    )
    telephone = models.CharField("Téléphone", max_length=30, blank=True)
    adresse = models.CharField("Adresse", max_length=255, blank=True)

    class Meta:
        verbose_name = "client"
        verbose_name_plural = "clients"

    def __str__(self):
        return self.utilisateur.get_full_name() or self.utilisateur.username
