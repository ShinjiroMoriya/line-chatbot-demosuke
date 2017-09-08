from django.core.management.base import BaseCommand
from line.einstein_vision import Train
from line.service import json_dumps


class Command(BaseCommand):
    def __init__(self, *args, **kwargs):
        self.train = Train()
        super(Command, self).__init__(*args, **kwargs)

    def add_arguments(self, parser):
        parser.add_argument('model_id', nargs='?', type=str)

    def handle(self, *args, **options):
        model_id = options.get('model_id')
        result = self.train.confirm(model_id)
        print(json_dumps(result))
