from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.exceptions import ValidationError
from django.db.models import Q, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from parc.models import Voiture

from .forms import PaiementForm, ReservationForm
from .models import Paiem, Reserv
from .services import creer_reserv, enregistrer_paiem


@login_required
def vue_creer_reserv(request, voiture_id):
    voiture = get_object_or_404(Voiture, pk=voiture_id, active=True)
    form = ReservationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        try:
            reserv = creer_reserv(
                utilisateur=request.user,
                voiture_id=voiture.pk,
                **form.cleaned_data,
            )
        except (ValidationError, Voiture.DoesNotExist) as erreur:
            if isinstance(erreur, ValidationError):
                form.add_error(None, erreur)
            else:
                messages.error(request, "Cette voiture n'est plus disponible.")
        else:
            messages.success(request, "Votre demande de réservation a été enregistrée.")
            return redirect("mes_reservations")
    return render(
        request, "reservations/formulaire.html", {"form": form, "voiture": voiture}
    )


@login_required
def vue_mes_reservations(request):
    reservations = Reserv.objects.filter(utilisateur=request.user).select_related("voiture")
    return render(
        request, "reservations/mes_reservations.html", {"reservations": reservations}
    )


def _est_personnel(utilisateur):
    return utilisateur.is_staff


@user_passes_test(_est_personnel)
def vue_gestion_reservations(request):
    reservations = Reserv.objects.select_related("utilisateur", "voiture").annotate(
        montant_recu=Sum(
            "paiements__montant", filter=Q(paiements__statut=Paiem.Statut.RECU)
        )
    )
    return render(
        request, "reservations/gestion.html", {"reservations": reservations}
    )


@require_POST
@user_passes_test(_est_personnel)
def vue_changer_statut(request, pk):
    reserv = get_object_or_404(Reserv, pk=pk)
    nouveau = request.POST.get("statut")
    if nouveau not in Reserv.TRANSITIONS.get(reserv.statut, set()):
        messages.error(request, "Cette transition de statut n'est pas autorisée.")
    else:
        reserv.statut = nouveau
        reserv.save(update_fields=["statut"])
        messages.success(request, "Le statut de la réservation a été mis à jour.")
    return redirect("gestion_reservations")


@require_POST
@user_passes_test(_est_personnel)
def vue_ajouter_paiement(request, pk):
    reserv = get_object_or_404(Reserv, pk=pk)
    form = PaiementForm(request.POST)
    if form.is_valid():
        try:
            enregistrer_paiem(reserv_id=reserv.pk, donnees=form.cleaned_data)
        except ValidationError as erreur:
            messages.error(request, " ".join(erreur.messages))
        else:
            messages.success(request, "Le paiement manuel a été enregistré.")
    else:
        messages.error(request, "Les informations du paiement sont invalides.")
    return redirect("gestion_reservations")
