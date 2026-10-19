from django import forms
from django.db.models import Sum

from reservations.models import Paiem, Reserv


class ReservChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, reserv):
        nom = reserv.utilisateur.get_full_name() or reserv.utilisateur.username
        return f"#{reserv.pk} — {reserv.voiture} — {nom} — {reserv.mont_t} Ar"


class PaiementGestionForm(forms.ModelForm):
    reserv = ReservChoiceField(
        label="Réservation",
        queryset=Reserv.objects.none(),
        empty_label="Choisir une réservation",
    )

    class Meta:
        model = Paiem
        fields = ("reserv", "montant", "date_paiem", "mode")
        widgets = {
            "date_paiem": forms.DateInput(attrs={"type": "date"}),
            "montant": forms.NumberInput(attrs={"min": "0.01", "step": "0.01"}),
        }

    def __init__(self, *args, reserv=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["reserv"].queryset = (
            Reserv.objects.select_related("voiture", "utilisateur").order_by("-cree_le")
        )
        if reserv:
            self.fields["reserv"].initial = reserv
            self.fields["reserv"].widget = forms.HiddenInput()
            self.fields["reserv"].disabled = True

    def clean_montant(self):
        montant = self.cleaned_data["montant"]
        reserv = self.cleaned_data.get("reserv")
        if reserv:
            deja_recu = reserv.paiements.filter(statut=Paiem.Statut.RECU).aggregate(
                total=Sum("montant")
            )["total"] or 0
            if montant + deja_recu > reserv.mont_t:
                raise forms.ValidationError(
                    "Le paiement dépasse le solde restant de cette réservation."
                )
        return montant
