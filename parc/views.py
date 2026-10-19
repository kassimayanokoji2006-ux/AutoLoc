from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Count, Q
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render, reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from reservations.models import Reserv

from .forms import VoitureForm
from .models import Favori, Voiture


def vue_accueil(request):
    voitures = Voiture.objects.filter(active=True).order_by("-cree_le")[:6]
    ids_favoris = (
        set(Favori.objects.filter(utilisateur=request.user).values_list("voiture_id", flat=True))
        if request.user.is_authenticated else set()
    )
    return render(
        request,
        "parc/accueil.html",
        {"voitures": voitures, "voitures_favorites": ids_favoris},
    )


def _decimal_parametre(valeur):
    if not valeur:
        return None
    try:
        nombre = Decimal(valeur)
        return nombre if nombre.is_finite() and nombre >= 0 else None
    except (InvalidOperation, TypeError):
        return None


def vue_voitures(request):
    voitures = Voiture.objects.filter(active=True)
    recherche = request.GET.get("q", "").strip()[:100]
    if recherche:
        voitures = voitures.filter(
            Q(marq__icontains=recherche)
            | Q(modl__icontains=recherche)
            | Q(description__icontains=recherche)
        )

    categories = request.GET.getlist("categ")
    categories_valides = [v for v in categories if v in Voiture.Categorie.values]
    if categories_valides:
        voitures = voitures.filter(categ__in=categories_valides)
    marques_demandees = request.GET.getlist("marq")[:20]
    marques_existantes = set(
        Voiture.objects.filter(active=True)
        .values_list("marq", flat=True)
        .distinct()
    )
    marques = [v for v in marques_demandees if v in marques_existantes]
    if marques:
        voitures = voitures.filter(marq__in=marques)
    carburants = request.GET.getlist("carburant")
    carburants_valides = [v for v in carburants if v in Voiture.Carburant.values]
    if carburants_valides:
        voitures = voitures.filter(carburant__in=carburants_valides)
    transmissions = request.GET.getlist("transmission")
    transmissions_valides = [v for v in transmissions if v in Voiture.Transmission.values]
    if transmissions_valides:
        voitures = voitures.filter(transmission__in=transmissions_valides)
    disponibles = request.GET.get("disponibles") == "1"
    if disponibles:
        aujourd_hui = timezone.localdate()
        occupees = Reserv.objects.filter(
            dat_deb__lte=aujourd_hui,
            dat_fin__gt=aujourd_hui,
            statut__in=[
                Reserv.Statut.ATTENTE,
                Reserv.Statut.CONFIRMEE,
                Reserv.Statut.EN_COURS,
            ],
        ).values("voiture_id")
        voitures = voitures.exclude(pk__in=occupees)
    prix_min = _decimal_parametre(request.GET.get("prix_min"))
    prix_max = _decimal_parametre(request.GET.get("prix_max"))
    if prix_min is not None:
        voitures = voitures.filter(prix_j__gte=prix_min)
    if prix_max is not None:
        voitures = voitures.filter(prix_j__lte=prix_max)

    uniquement_favoris = request.GET.get("favoris") == "1"
    if uniquement_favoris and request.user.is_authenticated:
        voitures = voitures.filter(favoris__utilisateur=request.user)
    elif uniquement_favoris:
        voitures = voitures.none()

    tri = request.GET.get("tri")
    tris = {
        "prix_croissant": ("prix_j", "pk"),
        "prix_decroissant": ("-prix_j", "pk"),
        "recentes": ("-cree_le", "pk"),
    }
    voitures = voitures.order_by(*tris.get(tri, ("-cree_le", "pk"))).distinct()
    nombre_voitures = voitures.count()
    pages = Paginator(voitures, 9)
    page_obj = pages.get_page(request.GET.get("page"))
    toutes_marques = Voiture.objects.filter(active=True).values("marq").annotate(
        nombre=Count("pk")
    ).order_by("marq")
    filtres_actifs = []
    parametres = request.GET.copy()
    parametres.pop("page", None)

    def ajouter_pastille(nom, valeur, libelle):
        restant = parametres.copy()
        valeurs = restant.getlist(nom)
        if len(valeurs) > 1:
            valeurs.remove(valeur)
            restant.setlist(nom, valeurs)
        else:
            restant.pop(nom, None)
        filtres_actifs.append(
            {"libelle": libelle, "url": f"?{restant.urlencode()}" if restant else reverse("catalogue")}
        )

    if recherche:
        ajouter_pastille("q", recherche, f"Recherche : {recherche}")
    for cle, libelle in Voiture.Categorie.choices:
        if cle in categories_valides:
            ajouter_pastille("categ", cle, libelle)
    for marque in marques:
        ajouter_pastille("marq", marque, marque)
    for cle, libelle in Voiture.Carburant.choices:
        if cle in carburants_valides:
            ajouter_pastille("carburant", cle, libelle)
    for cle, libelle in Voiture.Transmission.choices:
        if cle in transmissions_valides:
            ajouter_pastille("transmission", cle, libelle)
    if request.GET.get("disponibles") == "1":
        ajouter_pastille("disponibles", "1", "Disponibles aujourd'hui")
    if uniquement_favoris:
        ajouter_pastille("favoris", "1", "Mes favoris")
    if prix_min is not None:
        ajouter_pastille("prix_min", request.GET["prix_min"], f"Min. {request.GET['prix_min']} Ar")
    if prix_max is not None:
        ajouter_pastille("prix_max", request.GET["prix_max"], f"Max. {request.GET['prix_max']} Ar")
    context = {
        "voitures": page_obj.object_list,
        "page_obj": page_obj,
        "query_sans_page": parametres.urlencode(),
        "nombre_voitures": nombre_voitures,
        "filtres_actifs": filtres_actifs,
        "categories": Voiture.Categorie.choices,
        "carburants": Voiture.Carburant.choices,
        "transmissions": Voiture.Transmission.choices,
        "toutes_marques": toutes_marques,
        "recherche": recherche,
        "prix_min": request.GET.get("prix_min", ""),
        "prix_max": request.GET.get("prix_max", ""),
        "tri": tri if tri in tris else "",
        "favoris_seuls": uniquement_favoris,
        "disponibles": disponibles,
        "categories_selectionnees": categories_valides,
        "marques_selectionnees": marques,
        "carburants_selectionnes": carburants_valides,
        "transmissions_selectionnees": transmissions_valides,
        "voitures_favorites": set(
            Favori.objects.filter(utilisateur=request.user).values_list("voiture_id", flat=True)
        ) if request.user.is_authenticated else set(),
    }
    return render(request, "parc/catalogue.html", context)


def vue_detail_voiture(request, pk):
    voiture = get_object_or_404(Voiture, pk=pk, active=True)
    favorite = request.user.is_authenticated and Favori.objects.filter(
        utilisateur=request.user, voiture=voiture
    ).exists()
    return render(
        request, "parc/detail.html", {"voiture": voiture, "est_favori": favorite}
    )


@require_POST
@login_required
def bascul_fav(request, pk):
    voiture = get_object_or_404(Voiture, pk=pk, active=True)
    favori, cree = Favori.objects.get_or_create(
        utilisateur=request.user, voiture=voiture
    )
    if not cree:
        favori.delete()
    return JsonResponse({"favori": cree})


def _est_personnel(utilisateur):
    return utilisateur.is_staff


@user_passes_test(_est_personnel)
def vue_ajouter_voiture(request):
    form = VoitureForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "La voiture a été ajoutée au parc.")
        return redirect("catalogue")
    return render(request, "parc/voiture_form.html", {"form": form})
