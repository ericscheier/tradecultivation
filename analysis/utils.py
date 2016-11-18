from django.db.models import Q
import itertools
import re
import json

import krakenex
from .models import Currency, Chain, Pair, ChainPair

# utility function
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
    
    # filter out pairs ending in .d
    p = re.compile(r'\.d')
    pair_names = [i for i in list(pairs["result"]) if p.search(i) is None]
    # pair_names = list(pairs["result"])
    
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
            pair_to_update.name = pair
            pair_to_update.altname = pair_data["altname"]
            pair_to_update.base_currency = Currency.objects.filter(name=pair_data["base"])[0]
            pair_to_update.quote_currency = Currency.objects.filter(name=pair_data["quote"])[0]
            pair_to_update.is_eligible = True
            
            pair_to_update.save()
            
    # also make sure we find any currencies that are no longer listed
    Pair.objects.exclude(name__in=pair_names).update(is_eligible=False)
    
    return Pair.objects.filter(is_eligible=True)

def calculateChains(portfolio_currency="XXBT", currencies=None, pairs=None, max_chain_length=5):
    
    # max_chain_length >= 7 takes extremely long time
    if pairs is None:
        pairs = Pair.objects.filter(is_eligible=True)
        # pairs = updatePairs()
    if currencies is None:
        currencies = Currency.objects.filter(is_eligible=True)
        
    # determine all possible permutations of currency orderings of all sizes excluding the base currency and not repeating any currency twice in a chain
    currency_names = [currency.name for currency in currencies if currency.name != portfolio_currency]
    
    pair_names = {pair.name:[pair.base_currency.name, pair.quote_currency.name] for pair in pairs}
    
    # for speed of testing
    # currency_names = currency_names[0:6]
    #
    possible_currency_pairs = list(itertools.combinations(currency_names,2))

    permutations = [list(c) for i in range(1, max_chain_length) for c in itertools.permutations(currency_names, i)]  
    # print("Calculated permutations")
    # for each permutation, go through trade by trade to determine whether there exists a pair that could enable that trade, starting from the base currency and returning to it
    possible_chains = []
    for permutation in permutations:
        # permutation.insert(0,portfolio_currency_name)
        permutation.append(portfolio_currency)
        
        chain = []
        chain_is_valid = True
        
        holding_currency = portfolio_currency
        
        for target_currency in permutation:
            if chain_is_valid:
                try:
                    transaction_pair = list(pair_names.keys())[list(pair_names.values()).index([holding_currency, target_currency])]
                    chain.append(transaction_pair)
                    holding_currency = target_currency
                except:
                    try:
                        transaction_pair = list(pair_names.keys())[list(pair_names.values()).index([target_currency, holding_currency])]
                        chain.append(transaction_pair)
                        holding_currency = target_currency
                    except:
                        chain_is_valid = False
                        # print("Ruled out a chain")
        if chain_is_valid:
            possible_chains.append(chain)
            # print("Found a chain!")
    
    
    return possible_chains
    
def createChain(pair_list):
    chain_length = len(pair_list)
    
    new_chain = Chain.objects.create(name=json.dumps(pair_list),
                                     length=chain_length)
    new_chain.save()
    
    chain_pairs = Pair.objects.filter(name__in=pair_list)
    for pair_name in pair_list:
        pair = chain_pairs.filter(name=pair_name)
        pair_index = pair_list.index(pair_name)+1
        new_chain_pair = ChainPair.objects.create(chain=new_chain,
                                                 pair=pair,
                                                 index=pair_index)
        new_chain_pair.save()
    
def updateChains(possible_chains=None):
    if possible_chains is None:
        possible_chains = calculateChains(max_chain_length=2)
        
    existing_chains = Chain.objects.filter(name__in=[json.dumps(i) for i in possible_chains])
    new_chains = 1
    obsolete_chains = Chain.objects.exclude(name__in=[json.dumps(i) for i in possible_chains]).update(is_eligible=False)
    
    
def filterChains():
    return
    
def eligiblePairs():
    return
    
