from django.core.management.base import BaseCommand
from line.einstein_vision import Datasets
import json


class Command(BaseCommand):
    def __init__(self, *args, **kwargs):
        self.datasets = Datasets()
        super(Command, self).__init__(*args, **kwargs)

    def handle(self, *args, **options):
        result = self.datasets.all()
        print(json.dumps(result, indent=4))
