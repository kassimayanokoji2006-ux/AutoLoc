from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator, MinValueValidator
from django.db import models


class Voiture(models.Model):
    class Categorie(models.TextChoices):
        BERLINE = "berline", "Berline"
        SUV = "suv", "SUV"
        CITADINE = "citadine", "Citadine"
        COUPE = "coupe", "Coupé"
        UTILITAIRE = "utilitaire", "Utilitaire"

    class Carburant(models.TextChoices):
        ESSENCE = "essence", "Essence"
        DIESEL = "diesel", "Diesel"
        HYBRIDE = "hybride", "Hybride"
        ELECTRIQUE = "electrique", "Électrique"

    class Transmission(models.TextChoices):
        MANUELLE = "manuelle", "Manuelle"
        AUTOMATIQUE = "automatique", "Automatique"

    marq = models.CharField("Marque", max_length=80)
    modl = models.CharField("Modèle", max_length=100)
    categ = models.CharField("Catégorie", max_length=20, choices=Categorie.choices)
    immat = models.CharField("Immatriculation", max_length=20, unique=True)
    description = models.TextField("Description", blank=True)
    prix_j = models.DecimalField(
        "Prix journalier (Ar)", max_digits=8, decimal_places=2, validators=[MinValueValidator(0.01)]
    )
    nb_places = models.PositiveSmallIntegerField("Nombre de places", default=5)
    carburant = models.CharField("Carburant", max_length=20, choices=Carburant.choices)
    transmission = models.CharField(
        "Transmission", max_length=20, choices=Transmission.choices
    )
    image = models.ImageField(
        "Image", upload_to="voitures/", blank=True,
        validators=[FileExtensionValidator(["jpg", "jpeg", "png", "webp"])],
    )
    active = models.BooleanField("Voiture active", default=True)
    cree_le = models.DateTimeField("Créée le", auto_now_add=True)

    class Meta:
        ordering = ("marq", "modl")
        verbose_name = "voiture"
        verbose_name_plural = "voitures"

    def clean(self):
        super().clean()
        if self.image and self.image.size > 5 * 1024 * 1024:
            raise ValidationError({"image": "L’image ne peut pas dépasser 5 Mo."})

    def __str__(self):
        return f"{self.marq} {self.modl}"


class Favori(models.Model):
    utilisateur = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="favoris"
    )
    voiture = models.ForeignKey(
        Voiture, on_delete=models.CASCADE, related_name="favoris"
    )
    cree_le = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("utilisateur", "voiture"), name="favori_utilisateur_voiture_unique"
            )
        ]
        verbose_name = "favori"
        verbose_name_plural = "favoris"

    def __str__(self):
        return f"{self.utilisateur} — {self.voiture}"
