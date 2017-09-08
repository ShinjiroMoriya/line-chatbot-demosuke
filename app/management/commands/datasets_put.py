from django.core.management.base import BaseCommand
from line.einstein_vision import Datasets
from line.service import json_dumps


class Command(BaseCommand):
    def __init__(self, *args, **kwargs):
        self.datasets = Datasets()
        super(Command, self).__init__(*args, **kwargs)

    def add_arguments(self, parser):
        parser.add_argument('--path', dest='path', nargs='?', type=str)
        parser.add_argument('--datasets', dest='datasets', nargs='?', type=str)

    def handle(self, *args, **options):
        path = options.get('path')
        datasets = options.get('datasets')
        result = self.datasets.put(datasets_id=datasets, path=path)
        print(json_dumps(result))
