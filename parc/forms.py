from django import forms

from .models import Voiture


class VoitureForm(forms.ModelForm):
    class Meta:
        model = Voiture
        fields = (
            "marq", "modl", "categ", "immat", "description", "prix_j",
            "nb_places", "carburant", "transmission", "image", "active",
        )
        widgets = {"description": forms.Textarea(attrs={"rows": 4})}
