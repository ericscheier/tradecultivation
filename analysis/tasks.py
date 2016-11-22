from __future__ import absolute_import

from celery import shared_task
from celery.signals import celeryd_after_setup
# from django.utils import timezone

from . import utils

@shared_task #(name='')
def prepare():
    currencies = utils.updateCurrencies()
    pairs = utils.updatePairs()
    possible_chains = utils.getChains()
    filtered_chains = utils.filterChains(possible_chains=possible_chains, max_chain_length=5)
    eligible_pairs = utils.eligiblePairs(filtered_chains=filtered_chains, max_chain_length=5)
    return eligible_pairs

@shared_task
def preBuild():
    harvested_pairs = utils.harvest()
    return harvested_pairs

@shared_task
#@celeryd_after_setup.update
def update():
    prepare()