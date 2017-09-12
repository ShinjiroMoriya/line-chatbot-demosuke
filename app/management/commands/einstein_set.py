import os
from django.core.management.base import BaseCommand
from line.einstein_vision import Datasets, Train
from line.service import json_dumps


class Command(BaseCommand):
    def __init__(self, *args, **kwargs):
        self.datasets = Datasets()
        self.train = Train()
        super(Command, self).__init__(*args, **kwargs)

    def add_arguments(self, parser):
        parser.add_argument('--path', dest='path', nargs='?', type=str)
        parser.add_argument('--name', dest='name', nargs='?', type=str)

    def handle(self, *args, **options):
        path = options.get('path')
        name = options.get('name')
        if os.path.isfile(path):
            result = self.datasets.upload(path=path, name=name)
            print(json_dumps(result))
            datasets_id = result.get('id')
            name = result.get('name')
            result = self.train.create(
                datasets_id=str(datasets_id), name=str(name))
            print(json_dumps(result))

        else:
            print('File does not exist')
