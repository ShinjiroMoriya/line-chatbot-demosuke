from django.db import models


class SfDictionary(models.Model):
    class Meta:
        db_table = 'dictionary__c'

    proper_noun = models.CharField(max_length=255, null=True, blank=True,
                                   db_column='proper_noun__c')
    reading = models.CharField(max_length=255, null=True, blank=True,
                               db_column='reading__c')
    attribute = models.CharField(max_length=255, null=True, blank=True,
                                 db_column='attribute__c')

    def __str__(self):
        return self.proper_noun
