from __future__ import absolute_import

from celery import shared_task
from celery.signals import celeryd_after_setup
# from django.utils import timezone


@shared_task #(name='')
def prepare():
    currencies = updateCurrencies()
    pairs = updatePairs()
    possible_chains = getChains()
    filtered_chains = filterChains(possible_chains=possible_chains, max_chain_length=5)
    eligible_pairs = eligiblePairs(filtered_chains=filtered_chains, max_chain_length=5)

@shared_task
def preBuild():
    return

@shared_task
@celeryd_after_setup.update
def update():
    prepare()