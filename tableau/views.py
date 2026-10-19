from django.contrib import messages
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.db.models import Count, Q, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from comptes.models import Client
from parc.forms import VoitureForm
from parc.models import Voiture
from reservations.models import Paiem, Reserv
from reservations.services import changer_statut_reserv, enregistrer_paiem

from .forms import PaiementGestionForm
from .permissions import personnel_requis
from .services import (
    archiver_voiture,
    donnees_tableau,
    reactiver_voiture,
)


def _page(request, elements, par_page=12):
    return Paginator(elements, par_page).get_page(request.GET.get("page"))


def _query_sans_page(request):
    parametres = request.GET.copy()
    parametres.pop("page", None)
    return parametres.urlencode()


@personnel_requis
def vue_tableau(request):
    return render(request, "tableau/index.html", donnees_tableau())


@personnel_requis
def vue_voitures(request):
    voitures = Voiture.objects.all()
    recherche = request.GET.get("q", "").strip()[:100]
    etat = request.GET.get("etat", "actives")
    if recherche:
        voitures = voitures.filter(
            Q(marq__icontains=recherche)
            | Q(modl__icontains=recherche)
            | Q(immat__icontains=recherche)
        )
    if etat == "actives":
        voitures = voitures.filter(active=True)
    elif etat == "archivees":
        voitures = voitures.filter(active=False)
    else:
        etat = "toutes"
    context = {
        "page_obj": _page(request, voitures.order_by("marq", "modl")),
        "recherche": recherche,
        "etat": etat,
        "query_sans_page": _query_sans_page(request),
    }
    return render(request, "tableau/voitures.html", context)


@personnel_requis
def vue_voiture_form(request, pk=None):
    voiture = get_object_or_404(Voiture, pk=pk) if pk else None
    form = VoitureForm(
        request.POST or None,
        request.FILES or None,
        instance=voiture,
    )
    if request.method == "POST" and form.is_valid():
        voiture = form.save()
        messages.success(
            request,
            "La voiture a été mise à jour." if pk else "La voiture a été ajoutée.",
        )
        return redirect("gestion_voiture_detail", pk=voiture.pk)
    return render(
        request,
        "tableau/voiture_form.html",
        {"form": form, "voiture": voiture},
    )


@personnel_requis
def vue_voiture_detail(request, pk):
    voiture = get_object_or_404(Voiture, pk=pk)
    reservations = voiture.reservations.select_related("utilisateur").order_by(
        "-cree_le"
    )[:8]
    return render(
        request,
        "tableau/voiture_detail.html",
        {"voiture": voiture, "reservations": reservations},
    )


@personnel_requis
@require_POST
def vue_voiture_etat(request, pk):
    voiture = get_object_or_404(Voiture, pk=pk)
    if voiture.active:
        archiver_voiture(voiture=voiture)
        messages.success(request, "La voiture a été archivée sans supprimer son historique.")
    else:
        reactiver_voiture(voiture=voiture)
        messages.success(request, "La voiture a été réactivée.")
    return redirect("gestion_voitures")


@personnel_requis
def vue_clients(request):
    clients = Client.objects.select_related("utilisateur").annotate(
        nombre_reservations=Count("utilisateur__reservations", distinct=True)
    )
    recherche = request.GET.get("q", "").strip()[:100]
    if recherche:
        clients = clients.filter(
            Q(utilisateur__first_name__icontains=recherche)
            | Q(utilisateur__last_name__icontains=recherche)
            | Q(utilisateur__username__icontains=recherche)
            | Q(utilisateur__email__icontains=recherche)
            | Q(telephone__icontains=recherche)
        )
    return render(
        request,
        "tableau/clients.html",
        {
            "page_obj": _page(request, clients.order_by("utilisateur__last_name")),
            "recherche": recherche,
            "query_sans_page": _query_sans_page(request),
        },
    )


@personnel_requis
def vue_client_detail(request, pk):
    client = get_object_or_404(Client.objects.select_related("utilisateur"), pk=pk)
    reservations = client.utilisateur.reservations.select_related("voiture").annotate(
        montant_recu=Sum(
            "paiements__montant",
            filter=Q(paiements__statut=Paiem.Statut.RECU),
        )
    )
    return render(
        request,
        "tableau/client_detail.html",
        {"client": client, "reservations": reservations},
    )


@personnel_requis
def vue_reservations(request):
    reservations = Reserv.objects.select_related("utilisateur", "voiture").annotate(
        montant_recu=Sum(
            "paiements__montant",
            filter=Q(paiements__statut=Paiem.Statut.RECU),
        )
    )
    statut = request.GET.get("statut", "")
    statuts_valides = Reserv.Statut.values
    if statut in statuts_valides:
        reservations = reservations.filter(statut=statut)
    else:
        statut = ""
    recherche = request.GET.get("q", "").strip()[:100]
    if recherche:
        reservations = reservations.filter(
            Q(utilisateur__first_name__icontains=recherche)
            | Q(utilisateur__last_name__icontains=recherche)
            | Q(utilisateur__username__icontains=recherche)
            | Q(voiture__marq__icontains=recherche)
            | Q(voiture__modl__icontains=recherche)
        )
    return render(
        request,
        "tableau/reservations.html",
        {
            "page_obj": _page(request, reservations.order_by("-cree_le")),
            "statut": statut,
            "statuts": Reserv.Statut.choices,
            "recherche": recherche,
            "query_sans_page": _query_sans_page(request),
        },
    )


@personnel_requis
def vue_reservation_detail(request, pk):
    reserv = get_object_or_404(
        Reserv.objects.select_related("utilisateur", "voiture"), pk=pk
    )
    paiements = reserv.paiements.order_by("-date_paiem", "-pk")
    montant_recu = paiements.filter(statut=Paiem.Statut.RECU).aggregate(
        total=Sum("montant")
    )["total"] or 0
    return render(
        request,
        "tableau/reservation_detail.html",
        {
            "reserv": reserv,
            "paiements": paiements,
            "montant_recu": montant_recu,
            "solde": max(reserv.mont_t - montant_recu, 0),
            "transitions": Reserv.TRANSITIONS.get(reserv.statut, set()),
            "statuts": Reserv.Statut.choices,
        },
    )


@personnel_requis
@require_POST
def vue_reservation_statut(request, pk):
    try:
        changer_statut_reserv(
            reserv_id=pk,
            statut=request.POST.get("statut", ""),
        )
    except (ValidationError, Reserv.DoesNotExist) as erreur:
        messages.error(
            request,
            " ".join(erreur.messages)
            if isinstance(erreur, ValidationError)
            else "Cette réservation n’existe plus.",
        )
    else:
        messages.success(request, "Le statut de la réservation a été modifié.")
    return redirect("gestion_reservation_detail", pk=pk)


@personnel_requis
def vue_paiements(request):
    paiements = Paiem.objects.select_related(
        "reserv", "reserv__voiture", "reserv__utilisateur"
    )
    return render(
        request,
        "tableau/paiements.html",
        {
            "page_obj": _page(request, paiements.order_by("-date_paiem", "-pk")),
            "query_sans_page": _query_sans_page(request),
        },
    )


@personnel_requis
def vue_paiement_form(request, reserv_id=None):
    reserv = get_object_or_404(Reserv, pk=reserv_id) if reserv_id else None
    form = PaiementGestionForm(request.POST or None, reserv=reserv)
    contexte = {"form": form, "reserv": reserv}
    if reserv:
        contexte["montant_recu"] = reserv.paiements.filter(
            statut=Paiem.Statut.RECU
        ).aggregate(total=Sum("montant"))["total"] or 0
        contexte["solde"] = max(reserv.mont_t - contexte["montant_recu"], 0)
        resume_reservations = [reserv]
    else:
        resume_reservations = (
            Reserv.objects.select_related("voiture", "utilisateur")
            .annotate(
                deja_recu=Sum(
                    "paiements__montant",
                    filter=Q(paiements__statut=Paiem.Statut.RECU),
                )
            )
            .order_by("-cree_le")
        )
    contexte["resume_reservations"] = {
        str(element.pk): {
            "total": str(element.mont_t),
            "paye": str(element.deja_recu or 0) if hasattr(element, "deja_recu") else str(
                element.paiements.filter(statut=Paiem.Statut.RECU).aggregate(
                    total=Sum("montant")
                )["total"] or 0
            ),
        }
        for element in resume_reservations
    }
    if request.method == "POST" and form.is_valid():
        try:
            enregistrer_paiem(
                reserv_id=form.cleaned_data["reserv"].pk,
                donnees={
                    cle: form.cleaned_data[cle]
                    for cle in ("montant", "date_paiem", "mode")
                },
            )
        except ValidationError as erreur:
            form.add_error("montant", erreur)
        else:
            messages.success(request, "Le paiement manuel a été enregistré.")
            return redirect("gestion_paiements")
    return render(request, "tableau/paiement_form.html", contexte)
