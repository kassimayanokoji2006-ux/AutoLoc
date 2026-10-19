from django import forms
from django.utils import timezone

from .models import Paiem


class ReservationForm(forms.Form):
    dat_deb = forms.DateField(
        label="Date de début", widget=forms.DateInput(attrs={"type": "date"})
    )
    dat_fin = forms.DateField(
        label="Date de fin", widget=forms.DateInput(attrs={"type": "date"})
    )

    def clean_dat_deb(self):
        dat_deb = self.cleaned_data["dat_deb"]
        if dat_deb < timezone.localdate():
            raise forms.ValidationError("La date de début ne peut pas être dans le passé.")
        return dat_deb


class PaiementForm(forms.ModelForm):
    class Meta:
        model = Paiem
        fields = ("montant", "date_paiem", "mode")
        widgets = {"date_paiem": forms.DateInput(attrs={"type": "date"})}
