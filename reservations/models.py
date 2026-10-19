from datetime import date
from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Sum


class Reserv(models.Model):
    class Statut(models.TextChoices):
        ATTENTE = "attente", "En attente"
        CONFIRMEE = "confirmee", "Confirmée"
        EN_COURS = "en_cours", "En cours"
        TERMINEE = "terminee", "Terminée"
        ANNULEE = "annulee", "Annulée"

    TRANSITIONS = {
        Statut.ATTENTE: {Statut.CONFIRMEE, Statut.ANNULEE},
        Statut.CONFIRMEE: {Statut.EN_COURS, Statut.ANNULEE},
        Statut.EN_COURS: {Statut.TERMINEE},
    }

    utilisateur = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="reservations"
    )
    voiture = models.ForeignKey(
        "parc.Voiture", on_delete=models.PROTECT, related_name="reservations"
    )
    dat_deb = models.DateField("Date de début")
    dat_fin = models.DateField("Date de fin (exclusive)")
    nb_j = models.PositiveIntegerField("Nombre de jours")
    mont_t = models.DecimalField("Montant total (Ar)", max_digits=10, decimal_places=2)
    statut = models.CharField(
        "Statut", max_length=12, choices=Statut.choices, default=Statut.ATTENTE
    )
    cree_le = models.DateTimeField("Créée le", auto_now_add=True)

    class Meta:
        ordering = ("-cree_le",)
        verbose_name = "réservation"
        verbose_name_plural = "réservations"
        constraints = [
            models.CheckConstraint(
                condition=models.Q(dat_fin__gt=models.F("dat_deb")),
                name="reservation_dates_coherentes",
            ),
            models.CheckConstraint(
                condition=models.Q(mont_t__gte=0),
                name="reservation_montant_non_negatif",
            ),
        ]

    @staticmethod
    def calc_prix(dat_deb, dat_fin, prix_j):
        if dat_fin <= dat_deb:
            raise ValidationError("La date de fin doit être postérieure à la date de début.")
        jours = (dat_fin - dat_deb).days
        return jours, (Decimal(prix_j) * jours).quantize(Decimal("0.01"))

    def clean(self):
        super().clean()
        if self.pk:
            ancien_statut = Reserv.objects.filter(pk=self.pk).values_list(
                "statut", flat=True
            ).first()
            if (
                ancien_statut
                and ancien_statut != self.statut
                and self.statut not in self.TRANSITIONS.get(ancien_statut, set())
            ):
                raise ValidationError({"statut": "Cette transition de statut n'est pas autorisée."})
        if self.dat_deb and self.dat_fin and self.dat_fin <= self.dat_deb:
            raise ValidationError({"dat_fin": "La fin doit être postérieure au début."})
        if self.voiture_id and self.dat_deb and self.dat_fin and self.statut != self.Statut.ANNULEE:
            chevauchement = Reserv.objects.filter(
                voiture=self.voiture,
                statut__in=[self.Statut.ATTENTE, self.Statut.CONFIRMEE, self.Statut.EN_COURS],
                dat_deb__lt=self.dat_fin,
                dat_fin__gt=self.dat_deb,
            ).exclude(pk=self.pk)
            if chevauchement.exists():
                raise ValidationError("Cette voiture est déjà réservée sur cette période.")

    def save(self, *args, **kwargs):
        if self.pk:
            ancien_statut = Reserv.objects.filter(pk=self.pk).values_list(
                "statut", flat=True
            ).first()
            if (
                ancien_statut
                and ancien_statut != self.statut
                and self.statut not in self.TRANSITIONS.get(ancien_statut, set())
            ):
                raise ValidationError("Cette transition de statut n'est pas autorisée.")
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Réservation #{self.pk} — {self.voiture}"


class Paiem(models.Model):
    class Mode(models.TextChoices):
        ESPECES = "especes", "Espèces"
        VIREMENT = "virement", "Virement"
        CARTE_SUR_PLACE = "carte_sur_place", "Carte sur place"
        AUTRE = "autre", "Autre"

    class Statut(models.TextChoices):
        RECU = "recu", "Reçu"
        REMBOURSE = "rembourse", "Remboursé"

    reserv = models.ForeignKey(Reserv, on_delete=models.PROTECT, related_name="paiements")
    montant = models.DecimalField(
        "Montant reçu (Ar)", max_digits=10, decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    date_paiem = models.DateField("Date du paiement", default=date.today)
    mode = models.CharField("Mode de paiement", max_length=20, choices=Mode.choices)
    statut = models.CharField(
        "Statut", max_length=12, choices=Statut.choices, default=Statut.RECU
    )

    class Meta:
        ordering = ("-date_paiem", "-pk")
        verbose_name = "paiement"
        verbose_name_plural = "paiements"

    def clean(self):
        super().clean()
        if not self.reserv_id or self.statut != self.Statut.RECU:
            return
        total = self.reserv.paiements.filter(statut=self.Statut.RECU).exclude(
            pk=self.pk
        ).aggregate(total=Sum("montant"))["total"] or Decimal("0.00")
        if self.montant and total + self.montant > self.reserv.mont_t:
            raise ValidationError({"montant": "Le paiement dépasse le solde restant."})

    def __str__(self):
        return f"{self.montant} Ar — réservation #{self.reserv_id}"
