from django.db.models import Q

import krakenex
from .models import Currency, Chain, Pair, ChainPair

def withoutKeys(d, keys):
    return {x: d[x] for x in d if x not in keys}

def updateCurrencies():
    api = krakenex.API()
    currencies = api.query_public("Assets")
    if currencies["error"]:
        return
        # return an error to Log
        # what is best return if error?
    currency_names = list(currencies["result"])
    for currency in currency_names:
        currency_data = currencies["result"][currency]
        currency_to_update = Currency.objects.filter(name=currency)
        if currency_to_update.count() > 1:
            # check to see if there are multiple of same currency in db
            return
        if not currency_to_update:
            # create the currency
            new_currency = Currency.objects.create(name=currency,
                                   altname=currency_data["altname"],
                                   decimals=currency_data["decimals"],
                                   display_decimals=currency_data["display_decimals"]
                                   )
            new_currency.save()
            
        else:
            # update the currency
            currency_to_update = currency_to_update[0]
            for (key, value) in withoutKeys(currency_data,{"aclass"}).items():
                setattr(currency_to_update, key, value)
            
    # also make sure we find any currencies that are no longer listed
    Currency.objects.exclude(name__in=currency_names).update(is_eligible=False)
    
    return Currency.objects.filter(is_eligible=True)
        
    

def updatePairs():
    #if currencies is None:
    #    currencies = updateCurrencies()
    api = krakenex.API()
    pairs = api.query_public("AssetPairs")
    if pairs["error"]:
        return
        # return an error to log
        # what to return if error?
    pair_names = list(pairs["result"])
    
    for pair in pair_names:
        pair_data = pairs["result"][pair]
        pair_to_update = Pair.objects.filter(name=pair)
        if pair_to_update.count() > 1:
            # check to see if there are multiple of same pair in db
            return
        if not pair_to_update:
            # create the pair
            new_pair = Pair.objects.create(name=pair,
                                           altname=pair_data["altname"],
                                           base_currency=Currency.objects.filter(name=pair_data["base"])[0],
                                           quote_currency=Currency.objects.filter(name=pair_data["quote"])[0],
                                           is_eligible=True
                                
                                   )
            new_pair.save()
            
        else:
            # update the pair
            pair_to_update = pair_to_update[0]
            print(pair_to_update.name)
            pair_to_update.name = pair
            pair_to_update.altname = pair_data["altname"]
            pair_to_update.base_currency = Currency.objects.filter(name=pair_data["base"])[0]
            pair_to_update.quote_currency = Currency.objects.filter(name=pair_data["quote"])[0]
            pair_to_update.is_eligible = True
            
            pair_to_update.save()
            
    # also make sure we find any currencies that are no longer listed
    Pair.objects.exclude(name__in=pair_names).update(is_eligible=False)
    
    return Pair.objects.filter(is_eligible=True)

def calculateChains(portfolio_currency_name="XXBT", pairs=None):
    if pairs is None:
        pairs = Pair.objects.filter(is_eligible=True)
        # pairs = updatePairs()
        
    current_currency_name = portfolio_currency_name
    chain_pairs = []
    
    possible_next_pairs = pairs.filter(
        (Q(base_currency__name=current_currency_name) |
        Q(quote_currency__name=current_currency_name)
        ).exclude(
            (Q(base_currency__name__in=chain_pairs) |
             Q(quote_currency__name__in=chain_pairs)
        ))
        
    
        
    chains = {}
    
    for starting_pair in starting_pairs:
        
    
    return chains
    
    
def updateChains(possible_chains=None):
    if possible_chains is None:
        possible_chains = calculateChains()
    return
    
    
def filterChains():
    return
    
def eligiblePairs():
    return
    
