from django.core.management.base import BaseCommand
import requests
import shutil
import os


class Command(BaseCommand):
    def __init__(self, *args, **kwargs):
        self.api_path = "https://www.googleapis.com/customsearch/v1"
        self.params = {
            "cx": os.environ.get('GOOGLE_CX'),
            "key": os.environ.get('GOOGLE_KEY'),
            "q": os.environ.get('GOOGLE_KEYWORDS'),
            "searchType": "image",
            "start": 1,
            "num": 10,
        }
        self.loop = 10
        self.image_idx = 0
        self.project_root = os.path.dirname(os.path.abspath(__file__))
        super(Command, self).__init__(*args, **kwargs)

    def handle(self, *args, **options):
        for x in range(self.loop):
            try:
                self.params.update({'start': self.params["num"] * x + 1})
                r = requests.get(self.api_path, self.params)
                r = r.json()
                items_json = r.get("items")
                for item_json in items_json:
                    path = os.path.join(self.project_root + '/images/' +
                                        str(self.image_idx) + '.png')
                    if not os.path.exists(self.project_root + '/images/'):
                        os.makedirs(self.project_root + '/images/')

                    r = requests.get(item_json['link'], stream=True)
                    if r.status_code == 200:
                        with open(path, 'wb') as f:
                            r.raw.decode_content = True
                            shutil.copyfileobj(r.raw, f)
                            self.image_idx += 1
            except:
                pass
