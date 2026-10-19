from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm

from .models import Client

Utilisateur = get_user_model()


class InscriptionForm(UserCreationForm):
    prenom = forms.CharField(label="Prénom", max_length=150)
    nom = forms.CharField(label="Nom", max_length=150)
    email = forms.EmailField(label="Adresse électronique")
    telephone = forms.CharField(label="Téléphone", max_length=30, required=False)

    class Meta(UserCreationForm.Meta):
        model = Utilisateur
        fields = ("username", "prenom", "nom", "email", "telephone")
        labels = {"username": "Nom d'utilisateur"}

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if Utilisateur.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("Cette adresse électronique est déjà utilisée.")
        return email

    def save(self, commit=True):
        utilisateur = super().save(commit=False)
        utilisateur.first_name = self.cleaned_data["prenom"]
        utilisateur.last_name = self.cleaned_data["nom"]
        utilisateur.email = self.cleaned_data["email"]
        if commit:
            utilisateur.save()
            Client.objects.create(
                utilisateur=utilisateur,
                telephone=self.cleaned_data["telephone"],
            )
        return utilisateur
