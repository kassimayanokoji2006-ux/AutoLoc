from django.contrib import messages
from django.contrib.auth import login
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods

from .forms import InscriptionForm


@require_http_methods(["GET", "POST"])
def inscription(request):
    if request.user.is_authenticated:
        return redirect("accueil")
    form = InscriptionForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        utilisateur = form.save()
        login(request, utilisateur)
        messages.success(request, "Votre compte a été créé.")
        return redirect("accueil")
    return render(request, "comptes/inscription.html", {"form": form})
