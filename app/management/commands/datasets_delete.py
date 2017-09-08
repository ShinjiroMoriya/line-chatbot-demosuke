from django.core.management.base import BaseCommand
from line.einstein_vision import Datasets


class Command(BaseCommand):
    def __init__(self, *args, **kwargs):
        self.datasets = Datasets()
        super(Command, self).__init__(*args, **kwargs)

    def add_arguments(self, parser):
        parser.add_argument('datasets_id', nargs='?', type=str)

    def handle(self, *args, **options):
        datasets_id = options.get('datasets_id')
        result = self.datasets.delete(datasets_id)
        print(result)
