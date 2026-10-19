from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Sum

from parc.models import Voiture

from .models import Paiem, Reserv


@transaction.atomic
def creer_reserv(*, utilisateur, voiture_id, dat_deb, dat_fin):
    voiture = Voiture.objects.select_for_update().get(pk=voiture_id, active=True)
    jours, montant = Reserv.calc_prix(dat_deb, dat_fin, voiture.prix_j)
    reserv = Reserv(
        utilisateur=utilisateur,
        voiture=voiture,
        dat_deb=dat_deb,
        dat_fin=dat_fin,
        nb_j=jours,
        mont_t=montant,
    )
    reserv.full_clean()
    reserv.save()
    return reserv


@transaction.atomic
def enregistrer_paiem(*, reserv_id, donnees):
    reserv = Reserv.objects.select_for_update().get(pk=reserv_id)
    deja_recu = reserv.paiements.filter(statut=Paiem.Statut.RECU).aggregate(
        total=Sum("montant")
    )["total"] or 0
    montant = donnees["montant"]
    if montant + deja_recu > reserv.mont_t:
        raise ValidationError("Le paiement dépasse le solde restant.")
    paiement = Paiem(reserv=reserv, **donnees)
    paiement.full_clean()
    paiement.save()
    return paiement


@transaction.atomic
def changer_statut_reserv(*, reserv_id, statut):
    reserv = Reserv.objects.select_for_update().get(pk=reserv_id)
    if statut not in Reserv.TRANSITIONS.get(reserv.statut, set()):
        raise ValidationError("Cette transition de statut n'est pas autorisée.")
    reserv.statut = statut
    reserv.full_clean()
    reserv.save(update_fields=["statut"])
    return reserv
