from django.core.management.base import BaseCommand
from dictionary.models import SfDictionary
from django.conf import settings
import csv


class Command(BaseCommand):
    def __init__(self, *args, **kwargs):
        super(Command, self).__init__(*args, **kwargs)

    def handle(self, *args, **options):
        b_dir = settings.BASE_DIR

        try:
            datas = SfDictionary.objects.all().values(
                'proper_noun', 'attribute', 'reading')

            dict_data = []

            for d in datas:
                dict_data.append({
                    'proper_noun': d.get('proper_noun'),
                    'blank1': '1111',
                    'blank2': '1111',
                    'blank3': '1',
                    'attribute': 'SF',
                    'blank4': '*',
                    'blank5': '*',
                    'blank6': '*',
                    'reading': d.get('reading'),
                    'blank7': '*',
                    'blank8': '*',
                })

            header = dict_data[0].keys()

            with open(b_dir + '/dict.csv', 'w') as f:
                writer = csv.DictWriter(f, header)
                for row in dict_data:
                    writer.writerow(row)
        except Exception as ex:
            print(ex)
            pass
