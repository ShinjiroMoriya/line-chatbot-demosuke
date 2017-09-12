from django.core.management.base import BaseCommand
from line.einstein_vision import Predict
from line.service import json_dumps


class Command(BaseCommand):
    def __init__(self, *args, **kwargs):
        self.predict = Predict()
        super(Command, self).__init__(*args, **kwargs)

    def add_arguments(self, parser):
        parser.add_argument('path', nargs='?', type=str)

    def handle(self, *args, **options):
        path = options.get('path')
        try:
            result = self.predict.file(path)
            print(json_dumps(result))
        except:
            pass
