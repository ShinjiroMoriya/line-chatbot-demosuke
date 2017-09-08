import os
from django.core.management.base import BaseCommand
from line.einstein_vision import Datasets
from line.service import json_dumps


class Command(BaseCommand):
    def __init__(self, *args, **kwargs):
        self.datasets = Datasets()
        super(Command, self).__init__(*args, **kwargs)

    def add_arguments(self, parser):
        parser.add_argument('--path', dest='path', nargs='?', type=str)
        parser.add_argument('--label', dest='label', nargs='?', type=str)
        parser.add_argument('--model', dest='model', nargs='?', type=str)

    def handle(self, *args, **options):
        path = options.get('path')
        label = options.get('label')
        model = options.get('model')
        if os.path.isfile(path):
            result = self.datasets.feedback(
                path=path, label=label, model_id=model)
            print(json_dumps(result))
        else:
            print('File does not exist')
