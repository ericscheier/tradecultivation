from django.db import models

# Create your models here.
class Currency(models.Model):
    name = models.CharField(null=False)
    altname = models.CharField(null=False)
    decimals = models.IntegerField(null=False)
    display_decimals = models.IntegerField(null=False)
    is_eligible = models.BooleanField(null=False, default=True)
    

class Pair(models.Model):
    name = models.CharField(null=False)
    altname = models.CharField(null=False)
    base_currency = models.ForeignKey(Currency, null=False)
    quote_currency = models.ForeignKey(Currency, null=False)
    is_eligible = models.BooleanField(null=False, default=False)
    
    def determineEligibility(self):
        # determine which pairs are in valid chains
        # is_eligible = False
        # if [is in a valid chain]:
        #   is_eligible = True
        # self.is_eligible = is_eligible
        # self.save()
        return
    

class Chain(models.Model):
    name = models.CharField(null=False)
    length = models.IntegerField(null=False)
    courtage = models.DecimalField(null=False, default=0)
    is_eligible = models.BooleanField(null=False, default=False)
    
    def determineEligibility(self, max_length):
        # is_eligible = True
        # if length > max_length:
        #   is_eligible = False
        # self.is_eligible = is_eligible
        # self.save()
        return
    
    def updateCourtage(self):
        # P(tn+1) = Ptn-1 - (Ptn-1 * t)
        # P0 = 1
        # Cost = 1 - P0/Pn
        # self.courtage = courtage
        # self.save()
        return
        
    
class ChainPair(models.Model):
    chain = models.ForeignKey(Chain, null=False)
    pair = models.ManyToManyField(Pair, null=False)
    index = models.IntegerField(null=False)
    
    
    
    class Meta:
        ordering = ('chain', 'place')