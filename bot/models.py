from datetime import datetime
from django.db import models


class SfBot(models.Model):
    class Meta:
        db_table = 'bot_response__c'

    question = models.CharField(max_length=255, null=True, blank=True,
                                db_column='question_sentence__c')
    access_point = models.CharField(max_length=255, null=True, blank=True,
                                    db_column='access_point__c')
    references = models.CharField(max_length=255, null=True, blank=True,
                                  db_column='references__c')
    reply_sentence = models.CharField(max_length=255, null=True, blank=True,
                                      db_column='reply_sentence__c')

    def __str__(self):
        return self.question

    @classmethod
    def get_bot_data(cls, question):
        return cls.objects.filter(question=question).first()


class SfNoBot(models.Model):
    class Meta:
        db_table = 'no_bot_response__c'

    contact_id = models.CharField(
        max_length=255, null=True, blank=True,
        db_column='contactid__c')
    question_date_and_time = models.DateTimeField(
        default=datetime.now,
        null=True, blank=True,
        db_column='question_date_and_time__c')
    question_sentence = models.TextField(
        null=True, blank=True,
        db_column='question_sentence__c')

    def __str__(self):
        return self.question_sentence

    @classmethod
    def create_no_bot(cls, data):
        obj, created = cls.objects.update_or_create(
            contact_id=data.get('contact_id'),
            question_sentence=data.get('question_sentence'),
        )
        return obj
