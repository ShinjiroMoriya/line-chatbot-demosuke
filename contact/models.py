from django.db import models


class SfContact(models.Model):
    class Meta:
        db_table = 'contact'

    sfid = models.CharField(
        max_length=255, null=True, blank=True,
        db_column='sfid')
    email = models.CharField(
        max_length=255, null=True, blank=True,
        db_column='email')
    line_id = models.CharField(
        max_length=255, null=True, blank=True,
        db_column='line_id__c')

    def __str__(self):
        return self.email

    @classmethod
    def get_by_email(cls, email):
        return cls.objects.filter(email=email).values().first()

    @classmethod
    def get_obj_by_email(cls, email):
        return cls.objects.filter(email=email)

    @classmethod
    def get_by_line_id(cls, line_id):
        return cls.objects.filter(line_id=line_id).values().first()
