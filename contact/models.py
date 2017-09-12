from django.db import models
from cloudinary import config as cloudinary_config
from line.cloudinary import image_upload


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
    image_path = models.CharField(
        max_length=255, null=True, blank=True,
        db_column='image_path__c')
    image_transmission_count = models.IntegerField(
        null=True, blank=True,
        db_column='image_transmission_count__c')

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

    @classmethod
    def image_upload_by_line_id(cls, line_id, file, message_id):
        data_obj = cls.objects.filter(line_id=line_id)
        data = data_obj.values().first()

        image_upload(file, message_id)

        cloudinary_path = ('https://res.cloudinary.com/' +
                           cloudinary_config().cloud_name + '/image/upload/')

        file_names = data.get('image_path')
        file_name = cloudinary_path + message_id + '.jpg'
        if not file_names:
            update_file = file_name
        else:
            update_file = file_names + ',' + file_name

        if not data.get('image_transmission_count'):
            file_count = 1
        else:
            file_count = data.get('image_transmission_count') + 1

        data_obj.update(
            image_path=update_file,
            image_transmission_count=file_count,
        )

    @classmethod
    def image_reset_by_line_id(cls, line_id):
        cls.objects.filter(line_id=line_id).update(
            image_transmission_count=0,
        )


class CountException(Exception):
    pass
