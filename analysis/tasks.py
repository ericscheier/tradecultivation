from __future__ import absolute_import

from celery import shared_task
from celery.signals import celeryd_after_setup
# from django.utils import timezone

from . import utils

@shared_task #(name='')
def prepare():
    '''
    Description: Runs preparation stage
    Inputs: None
    Output: A list of eligible pairs that will be used in the pre-build stage
    '''
    currencies = utils.updateCurrencies()
    pairs = utils.updatePairs()
    possible_chains = utils.getChains()
    filtered_chains = utils.filterChains(possible_chains=possible_chains, max_chain_length=5)
    eligible_pairs = utils.eligiblePairs(filtered_chains=filtered_chains, max_chain_length=5)
    return eligible_pairs

@shared_task
def preBuild():
    '''
    Description: Runs pre-build stage
    Inputs: None
    Output: A list of dictionary objects containing the characteristics of the pairs that will be used in the Build stage
    '''
    harvested_pairs = utils.harvest()
    return harvested_pairs

@shared_task
def build():
    '''
    Description: Runs build stage
    Inputs: None
    Output: A list of dictionary objects containing the valid chains, ordered by Net ROI
    '''
    trimmed_chains = utils.trim()
    return trimmed_chains

@shared_task
#@celeryd_after_setup.update
def update():
    '''
    Description: Runs essential functions upon application startup. Currently not functional.
    Inputs: None
    Output: None
    '''
    prepare()