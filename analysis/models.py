from django.db import models
import json

# Create your models here.
class Currency(models.Model):
    name = models.CharField(null=False, max_length=100)
    altname = models.CharField(null=False, max_length=100)
    decimals = models.IntegerField(null=False)
    display_decimals = models.IntegerField(null=False)
    is_eligible = models.BooleanField(null=False, default=True)
    

class Pair(models.Model):
    name = models.CharField(null=False, max_length=100)
    altname = models.CharField(null=False, max_length=100)
    base_currency = models.ForeignKey(Currency, null=False, related_name="base_currency")
    quote_currency = models.ForeignKey(Currency, null=False, related_name="quote_currency")
    volume=models.DecimalField(null=True, decimal_places=8, max_digits=20)
    current_bid_price=models.DecimalField(null=True, decimal_places=8, max_digits=20)
    current_ask_price=models.DecimalField(null=True, decimal_places=8, max_digits=20)
    num_of_trades=models.DecimalField(null=True, decimal_places=8, max_digits=20)
    minimum_volume = models.DecimalField(null=False, decimal_places=8, max_digits=20, default=0)
    is_eligible = models.BooleanField(null=False, default=False)
    survives_harvest = models.BooleanField(null=False, default=False)
    

class Chain(models.Model):
    name = models.CharField(null=False, max_length=1000)
    length = models.IntegerField(null=False)
    courtage = models.DecimalField(null=False, decimal_places=8, max_digits=20, default=0)
    is_eligible = models.BooleanField(null=False, default=False)
    
    def setName(self, pair_list):
        self.name = json.dumps(pair_list)
        
    def getName(self):
        return json.loads(self.name)
    
    
    def updateCourtage(self, courtage_percent):
        length = self.length
        initial_value = 1
        prior_value = initial_value
        for t in range(0,length):
            resulting_value = prior_value - (prior_value * courtage_percent)
            prior_value = resulting_value
        courtage_cost = 1 - (resulting_value/initial_value)
        self.courtage = courtage_cost
        self.save()
        
    
class ChainPair(models.Model):
    chain = models.ForeignKey(Chain, null=False)
    pair = models.ManyToManyField(Pair)
    index = models.IntegerField()
    
    
    
    class Meta:
        ordering = ('chain', 'index')