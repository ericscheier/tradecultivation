from django.db.models import Q
import itertools
import re
import json
import decimal

import krakenex
from .models import Currency, Chain, Pair, ChainPair
from django.conf import settings

# Utility function
def withoutKeys(d, keys):
    '''
    Description: Utility function that removes entries from a dictionary based on user-defined keys
    Inputs:
        d: A dictionary object
        keys: A list or dictionary of keys in d to be excluded
    Output: The dictionary "d" without keys "keys"
    '''
    return {x: d[x] for x in d if x not in keys}

def updateCurrencies():
    '''
    Description: Updates the currency objects from the kraken server
    Inputs: None
    Output: A QuerySet of eligible currencies for trading
    '''
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
            print("creating currency: "+str(currency))
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
    '''
    Description: Updates the pairs from the kraken server
    Inputs: None
    Output: A QuerySet of pairs eligible for trading
    '''
    #if currencies is None:
    #    currencies = updateCurrencies()
    chains_need_updating = False
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
            print("creating pair: "+str(pair))
            new_pair = Pair.objects.create(name=pair,
                                           altname=pair_data["altname"],
                                           base_currency=Currency.objects.filter(name=pair_data["base"])[0],
                                           quote_currency=Currency.objects.filter(name=pair_data["quote"])[0],
                                           is_eligible=True
                                
                                   )
            new_pair.save()
            chains_need_updating = True
            
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
    exclude_pairs = Pair.objects.exclude(name__in=pair_names)
    if exclude_pairs:
        exclude_pairs.update(is_eligible=False)
        chains_need_updating = True
    
    # Automatically update chains if a pair is added or removed
    if chains_need_updating:
        updateChains()
    
    return Pair.objects.filter(is_eligible=True)

def calculateChains(portfolio_currency="XXBT", currencies=None, pairs=None, max_chain_length=None):
    '''
    Description: Calculates all of the possible chains to trade from a base currency back into itself without using the same pair twice. There is a pair for each transaction, so chains to a single currency and back contain the same pair twice (e.g. [XXBTZJPY, XXBTZJPY])
    Inputs:
        portfolio_currency: String, the currency which all chains should start and end with
        currencies: QuerySet, the eligible currencies to be traded
        pairs: QuerySet, the eligible pairs to make chains from
        max_chain_length: Integer, the maximum transactions that chains should include
    Output: A list of lists, each list is a valid chain of pairs
    '''
    # max_chain_length >= 7 takes extremely long time
    if max_chain_length is None:
        max_chain_length = settings.MAX_CHAIN_LENGTH
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
    '''
    Description: Create a new chain from a list of pairs. Used internally when updating chains.
    Inputs:
        pair_list: list of pairs representing a valid chain.
    Output: None
    '''
    chain_length = len(pair_list)
    
    new_chain = Chain.objects.create(name=json.dumps(pair_list),
                                     length=chain_length,
                                     is_eligible=True)
    new_chain.updateCourtage(courtage_percent=0.003)
    new_chain.save()
    
    chain_pairs = Pair.objects.filter(name__in=pair_list)
    if chain_length==2 and pair_list[0]==pair_list[1]:
        # chains of length 2 must have same pair for both steps
        # do first pair
        pair_name = pair_list [0]
        pair = chain_pairs.filter(name=pair_name).first()
        pair_index = 1
        new_chain_pair = ChainPair.objects.create(chain=new_chain,
                                                  pair=pair,
                                                  index=pair_index)
        new_chain_pair.save()
        # pair.chainpair_set.add(new_chain_pair)
        
        pair_index = 2
        another_chain_pair = ChainPair.objects.create(chain=new_chain,
                                                      pair=pair,
                                                  index=pair_index)
        another_chain_pair.save()
        # pair.chainpair_set.add(another_chain_pair)
    else:
        for pair_name in pair_list:
            pair = chain_pairs.filter(name=pair_name).first()
            pair_index = pair_list.index(pair_name)+1
            new_chain_pair = ChainPair.objects.create(chain=new_chain,
                                                      pair=pair,
                                                      index=pair_index)
            new_chain_pair.save()
            # pair.chainpair_set.add(new_chain_pair)
        
    
def updateChains(possible_chains=None):
    '''
    Description: Updates databased of chains to reflect newly calculated chains
    Inputs:
        possible_chains: List of lists, each list is an ordered list of pairs denoting a valid chain
    Output: possible_chains, same as input
    '''
    if possible_chains is None:
        possible_chains = calculateChains()
        
    # possible_chains_list = [json.dumps(i) for i in possible_chains]

    existing_chains = Chain.objects.filter(name__in=[json.dumps(i) for i in possible_chains])
        
    for existing_chain in existing_chains:
        if existing_chain.getName() in possible_chains:
            existing_chain.is_eligible=True
            existing_chain.save()
        existing_chain.updateCourtage(courtage_percent=0.003)
        
    
    existing_chains_list = [x.getName() for x in existing_chains]
    new_chains = [x for x in possible_chains if x not in existing_chains_list]
    
    for new_chain in new_chains:
        print("creating chain: "+str(new_chain))
        createChain(new_chain)
    
    obsolete_chains = Chain.objects.exclude(name__in=[json.dumps(i) for i in possible_chains]).update(is_eligible=False)
    
    
    
    return possible_chains

def getChains():
    '''
    Description: Utility function to load valid chains into memory
    Inputs: None
    Output: QuerySet of eligible chains
    '''
    return Chain.objects.filter(is_eligible=True)
    
    
def filterChains(possible_chains=None, max_chain_length=None):
    '''
    Description: Returns chains only with desired properties
    Inputs:
        possible_chains: List of lists, each list is an ordered list of pairs denoting a valid chain
        max_chain_length: Integer, maximum # of transactions or pairs to be in a chain (math is the same for both concepts)
    Output: List of lists, each list an ordered list of pairs denoting a valid chain that meets the filter criteria
    '''
    if max_chain_length is None:
        max_chain_length = settings.MAX_CHAIN_LENGTH
    if possible_chains is None:
        possible_chains = getChains()
        
    filtered_chains = [chain for chain in possible_chains if chain.length <= max_chain_length]
    return filtered_chains
    
def eligiblePairs(filtered_chains=None, max_chain_length=None):
    '''
    Description: Determines which pairs are eligible for trading and updates their status in the database accordingly
    Inputs:
        filtered_chains: List of lists, each list an ordered list of pairs denoting a valid chain that meets the filter criteria
        max_chain_length: Integer, maximum # of transactions or pairs to be in a chain (math is the same for both concepts). For passing through to filterChains
    Output: List of pairs that are part of an eligible chain
    '''
    if max_chain_length is None:
        max_chain_length = settings.MAX_CHAIN_LENGTH
    if filtered_chains is None:
        filtered_chains = filterChains(max_chain_length=max_chain_length)
        
    flattened_list = [pair for chain in filtered_chains for pair in chain.getName()]
    eligible_pairs = list(set(flattened_list))
    
    Pair.objects.filter(name__in=eligible_pairs).update(is_eligible=True)
    Pair.objects.exclude(name__in=eligible_pairs).update(is_eligible=False)
    
    return eligible_pairs


def harvest(eligible_pairs=None):
    '''
    Description: Updates per-pair values from the kraken exchange, such as Volume and Bid Price
    Inputs:
        eligible_pairs: List, pairs that are eligible for trading in a valid chain
    Output: List of Dictionaries, each an updated pair object and all of its values
    '''
    if eligible_pairs is None:
        eligible_pairs = eligiblePairs()
        
    # verify kraken server time
    # call kraken API for eligible pairs
    request = {"pair":','.join(eligible_pairs)}
    api = krakenex.API()
    tickers = api.query_public("Ticker", req=request)
    if tickers["error"]:
        return
    for pair in eligible_pairs:
        ticker = tickers["result"][pair]
        pair_to_update = Pair.objects.filter(name=pair)
        
        pair_to_update.update(volume=float(ticker["v"][1]))
        pair_to_update.update(current_bid_price=float(ticker["b"][0]))
        pair_to_update.update(current_bid_volume=float(ticker["b"][2]))
        pair_to_update.update(current_ask_price=float(ticker["a"][0]))
        pair_to_update.update(current_ask_volume=float(ticker["a"][2]))
        pair_to_update.update(num_of_trades=int(ticker["t"][1]))
        # <pair_name> = pair name
        # a = ask array(<price>, <whole lot volume>, <lot volume>),
        # b = bid array(<price>, <whole lot volume>, <lot volume>),
        # c = last trade closed array(<price>, <lot volume>),
        # v = volume array(<today>, <last 24 hours>),
        # p = volume weighted average price array(<today>, <last 24 hours>),
        # t = number of trades array(<today>, <last 24 hours>),
        # l = low array(<today>, <last 24 hours>),
        # h = high array(<today>, <last 24 hours>),
        # o = today's opening price
    # update pairs info in the db
    harvested_pairs = Pair.objects.filter(name__in=eligible_pairs)
    
    return harvested_pairs.values()

def trim(harvested_pairs=None, filtered_chains=None, currencies=None, max_chain_length=None,portfolio_currency="XXBT",min_investment=None):
    '''
    Description: Determines Gross ROI, Net ROI, and Maximum Investment Potential for each chain
    Inputs:
        harvested_pairs: List, of pairs of same format as harvest() result
        filtered_chains: QuerySet of chains of same format as filterChains() result
        currencies: QuerySet, valid currencies for trading
        max_chain_length: Integer, max number of transactions desired per chain
        portfolio_currency: String, name of currency that portfolio is denoted in
        min_investment: Float, minimum amount of portfolio_currency that should be invested per chain
    Output: A List of Dictionaries that are above the minimum investment criteria and ordered by Net ROI for the chain.
    '''
    '''
        https://support.kraken.com/hc/en-us/articles/203053186-Currency-Exchange-Buying-Selling-and-Currency-Pair-Selection
        
        In currency exchange, there is always one currency that is bought and one that is sold (the sold currency is used to purchase the bought currency). The currencies bought and sold are determined by two things in the order form. First, whether the "buy" or "sell" button on the order form is selected, and second, which currency pair is selected. If you want to buy or sell the second currency in a pair (the quote currency), you have to think backwards, since the "buy" button will actually sell the quote currency in exchange for the base currency and the "sell" button will buy the quote currency using the base currency. Here's a summary.
        
        If the "buy" button is selected and currency pair x/y is selected, then currency x will be bought and currency y sold.
        
        If the "sell" button is selected and currency pair x/y is selected, then currency x will be sold and currency y will be bought.
    '''
    if max_chain_length is None:
        max_chain_length = settings.MAX_CHAIN_LENGTH
    if min_investment is None:
        min_investment = settings.MIN_INVESTMENT
    if filtered_chains is None:
        filtered_chains = list(filterChains(max_chain_length=max_chain_length))
    if harvested_pairs is None:
        harvested_pairs = harvest()
    if currencies is None:
        currencies = Currency.objects.filter(is_eligible=True)
        
    for chain in filtered_chains:
        initial_capital = min_investment
        max_investment = None
        holding_capital = initial_capital
        holding_currency = currencies.filter(name=portfolio_currency)[0].pk
        for pair in chain.getName():
            pair_specs = list(harvested_pairs.filter(name=pair))[0]
            base_currency = pair_specs['base_currency_id']
            quote_currency = pair_specs['quote_currency_id']
            if holding_currency == base_currency:
                # we need to sell base
                # selling at the bid sells the base currency to get the quote currency
                # so if we already have the base currency, we want the quote currency, we need to SELL at the BID:               
                holding_capital = holding_capital * pair_specs['current_bid_price']
                
                if max_investment is None:
                    max_investment = pair_specs['current_bid_volume']
                max_investment = min(max_investment * pair_specs['current_bid_price'], pair_specs['current_bid_volume'])
                
                
                holding_currency = quote_currency
            elif holding_currency == quote_currency:
                # we need to buy base
                # buying at the ask sells the quote currency to get the base currency
                # if we already have the quote currency, we want the base currency, we need to BUY at the ASK
                holding_capital = holding_capital/pair_specs['current_ask_price']
                
                if max_investment is None:
                    max_investment = pair_specs['current_ask_volume'] * pair_specs['current_ask_price']
                max_investment = min(max_investment/pair_specs['current_ask_price'], pair_specs['current_ask_volume'])
                
                
                holding_currency = base_currency
            else:
                # uh-oh, invalid chain somehow
                return
        groi = (holding_capital - initial_capital)/initial_capital
        nroi = groi - decimal.Decimal(chain.courtage)
        
        chain.groi=groi
        chain.nroi=nroi
        # chain.is_eligible=valid_chain
        chain.max_investment=max_investment
        chain.save()
        
    return getChains().filter(max_investment__gte=min_investment).order_by('nroi')

def dry(harvested_chains=None):
    '''
    Description: Determines the transactions that need to be taken based on the presence of valid chains
    Inputs:
        harvested_chains: chains that meet the volume and returns criteria
    Output: A List of dictionaries, each defining transactions that need to be taken (buy or sell)
    '''
    if harvested_chains is None:
        harvested_chains = trim()
        
    transactions = [i.getTransactions() for i in harvested_chains]
    
    return transactions
    