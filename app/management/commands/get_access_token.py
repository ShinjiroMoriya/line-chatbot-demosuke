from django.core.management.base import BaseCommand
from line.einstein_vision import EinsteinVisionApi


class Command(BaseCommand):
    def __init__(self, *args, **kwargs):
        self.einstein = EinsteinVisionApi()
        super(Command, self).__init__(*args, **kwargs)

    def handle(self, *args, **options):
        result = self.einstein.get_access_token()
        print(result)
