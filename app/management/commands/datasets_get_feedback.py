from django.core.management.base import BaseCommand
from line.einstein_vision import Datasets
from line.service import json_dumps


class Command(BaseCommand):
    def __init__(self, *args, **kwargs):
        self.datasets = Datasets()
        super(Command, self).__init__(*args, **kwargs)

    def add_arguments(self, parser):
        parser.add_argument('datasets', nargs='?', type=str)

    def handle(self, *args, **options):
        datasets_id = options.get('datasets')
        result = self.datasets.get_feedback(datasets_id=datasets_id)
        print(json_dumps(result))
