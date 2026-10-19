from django.db import transaction
from django.db.models import Count, Q, Sum
from django.utils import timezone

from parc.models import Voiture
from reservations.models import Paiem, Reserv


def donnees_tableau():
    aujourd_hui = timezone.localdate()
    reservations_actives = Reserv.objects.filter(
        statut__in=[
            Reserv.Statut.ATTENTE,
            Reserv.Statut.CONFIRMEE,
            Reserv.Statut.EN_COURS,
        ]
    )
    voitures_occupees = reservations_actives.filter(
        dat_deb__lte=aujourd_hui,
        dat_fin__gt=aujourd_hui,
        voiture__active=True,
    ).values("voiture_id")
    compteurs = dict(
        Reserv.objects.values("statut")
        .annotate(nombre=Count("pk"))
        .values_list("statut", "nombre")
    )
    total_reservations = sum(compteurs.values())
    graphique_statuts = [
        {
            "cle": cle,
            "libelle": libelle,
            "nombre": compteurs.get(cle, 0),
            "pourcentage": round(compteurs.get(cle, 0) * 100 / total_reservations)
            if total_reservations
            else 0,
        }
        for cle, libelle in Reserv.Statut.choices
    ]
    nb_voitures = Voiture.objects.filter(active=True).count()
    revenus = (
        Paiem.objects.filter(statut=Paiem.Statut.RECU).aggregate(total=Sum("montant"))[
            "total"
        ]
        or 0
    )
    soldes = sum(
        max(reserv.mont_t - (reserv.montant_recu or 0), 0)
        for reserv in Reserv.objects.exclude(statut=Reserv.Statut.ANNULEE).annotate(
            montant_recu=Sum(
                "paiements__montant",
                filter=Q(paiements__statut=Paiem.Statut.RECU),
            )
        )
    )
    return {
        "nb_voitures": nb_voitures,
        "nb_disponibles": nb_voitures - voitures_occupees.distinct().count(),
        "nb_attente": compteurs.get(Reserv.Statut.ATTENTE, 0),
        "nb_confirmees": compteurs.get(Reserv.Statut.CONFIRMEE, 0),
        "nb_en_cours": compteurs.get(Reserv.Statut.EN_COURS, 0),
        "revenus": revenus,
        "soldes": soldes,
        "dernieres_reservations": Reserv.objects.select_related(
            "utilisateur", "voiture"
        ).order_by("-cree_le")[:8],
        "graphique_statuts": graphique_statuts,
    }


@transaction.atomic
def archiver_voiture(*, voiture):
    voiture = Voiture.objects.select_for_update().get(pk=voiture.pk)
    voiture.active = False
    voiture.save(update_fields=["active"])
    return voiture


@transaction.atomic
def reactiver_voiture(*, voiture):
    voiture = Voiture.objects.select_for_update().get(pk=voiture.pk)
    voiture.active = True
    voiture.save(update_fields=["active"])
    return voiture
