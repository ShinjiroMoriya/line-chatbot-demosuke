import os
import time
import jwt
import requests
from requests_toolbelt import MultipartEncoder, MultipartEncoderMonitor
from django.conf import settings as st
from datetime import datetime, timedelta
from base64 import b64encode
from clint.textui.progress import Bar as ProgressBar
from line.service import json_loads


class EinsteinVisionApi(object):
    def __init__(self):
        self.url = st.EINSTEIN_VISION_URL + st.EINSTEIN_VISION_API_VERSION
        self.req_url = self.url + '/oauth2/token'
        self.account_id = st.EINSTEIN_VISION_ACCOUNT_ID
        self.private_key = st.EINSTEIN_VISION_PRIVATE_KEY

        exp_time = datetime.now() + timedelta(minutes=30)
        exp_time = int(time.mktime(exp_time.timetuple()))

        payload = {
            'sub': self.account_id,
            'aud': self.req_url,
            'exp': exp_time,
        }
        self.assertion = jwt.encode(payload, self.private_key,
                                    algorithm='RS256')

    def get_access_token(self):
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
        }
        data = {
            'grant_type': 'urn:ietf:params:oauth:grant-type:jwt-bearer',
            'assertion': self.assertion,
        }
        result = requests.post(url=self.req_url, headers=headers, data=data)
        if result.status_code != 200:
            return None
        result = json_loads(result.content)
        return result.get('access_token')

    @staticmethod
    def create_callback(encoder):
        bar = ProgressBar(expected_size=encoder, filled_char='=')

        def callback(monitor):
            bar.show(monitor.bytes_read)

        return callback

    def post_proggress(self, req_url, fields):
        encoder = MultipartEncoder(fields)
        callback = self.create_callback(encoder.len)
        monitor = MultipartEncoderMonitor(encoder, callback)
        headers = {
            'Content-Type': monitor.content_type,
            'Authorization': 'Bearer ' + self.get_access_token(),
            'Cache-Control': 'no-cache',
        }
        r = requests.post(url=self.url + req_url, data=monitor, headers=headers)
        result = json_loads(r.content)
        if r.status_code != 200:
            return result.get('message')

        return result

    def get_requests(self, req_url):
        headers = {
            'Authorization': 'Bearer ' + self.get_access_token(),
            'Cache-Control': 'no-cache',
        }
        r = requests.get(url=self.url + req_url, headers=headers)
        result = json_loads(r.content)
        if r.status_code != 200:
            return result.get('message')

        return result

    def post_requests(self, req_url, fields):
        multipart = MultipartEncoder(fields)
        data = multipart.to_string()
        headers = {
            'Content-Type': multipart.content_type,
            'Authorization': 'Bearer ' + self.get_access_token(),
            'Cache-Control': 'no-cache',
        }
        r = requests.post(url=self.url + req_url, headers=headers, data=data)
        result = json_loads(r.content)
        if r.status_code != 200:
            return result.get('message')

        return result

    def put_requests(self, req_url, fields):
        multipart = MultipartEncoder(fields)
        data = multipart.to_string()
        headers = {
            'Content-Type': multipart.content_type,
            'Authorization': 'Bearer ' + self.get_access_token(),
            'Cache-Control': 'no-cache',
        }
        r = requests.put(url=self.url + req_url, headers=headers, data=data)
        result = json_loads(r.content)
        if r.status_code != 200:
            return result.get('message')

        return result

    def delete_requests(self, req_url):
        headers = {
            'Authorization': 'Bearer ' + self.get_access_token(),
            'Cache-Control': 'no-cache',
        }
        r = requests.delete(url=self.url + req_url, headers=headers)
        if r.status_code != 200:
            return 'Not delete'
        return 'Deleted'


class Datasets(EinsteinVisionApi):
    def upload(self, path, name):
        if not os.path.isfile(path):
            return None
        req_url = '/vision/datasets/upload/sync'
        fields = {
            'name': name,
            'type': 'image',
            'data': ('file', open(path, 'rb'), 'application/zip'),
        }
        return self.post_proggress(req_url, fields)

    def put(self, datasets_id, path):
        if not os.path.isfile(path):
            return None
        req_url = '/vision/datasets/' + datasets_id + '/upload'
        fields = {
            'data': ('file', open(path, 'rb'), 'application/zip'),
        }
        return self.put_requests(req_url, fields)

    def delete(self, datasets_id):
        req_url = '/vision/datasets/' + str(datasets_id)
        return self.delete_requests(req_url)

    def all(self):
        req_url = '/vision/datasets'
        return self.get_requests(req_url)

    def confirm(self, datasets_id):
        req_url = '/vision/datasets/' + str(datasets_id)
        return self.get_requests(req_url)

    def feedback(self, path, label, model_id):
        if not os.path.isfile(path):
            return None
        req_url = '/vision/feedback'
        fields = {
            'modelId': model_id,
            'expectedLabel': label,
            'data': ('file', open(path, 'rb'), 'application/octet-stream'),
            'name': os.path.basename(path),
        }
        return self.post_requests(req_url, fields)

    def get_feedback(self, datasets_id):
        req_url = ('/vision/datasets/' + datasets_id +
                   '/examples?source=feedback')
        return self.get_requests(req_url)


class Train(EinsteinVisionApi):
    def create(self, datasets_id, model_name):
        req_url = '/vision/train'
        fields = {
            'name': model_name,
            'datasetId': datasets_id,
        }
        return self.post_requests(req_url, fields)

    def retrain(self, model_id):
        req_url = '/vision/retrain'
        fields = {
            'modelId': model_id,
        }
        return self.post_requests(req_url, fields)

    def confirm(self, model_id):
        req_url = '/vision/train/' + str(model_id)
        return self.get_requests(req_url)


class Models(EinsteinVisionApi):
    def get(self, model_id):
        req_url = '/vision/models/' + model_id
        return self.get_requests(req_url)

    def lc(self, model_id):
        req_url = '/vision/models/' + model_id + '/lc'
        return self.get_requests(req_url)


class Predict(EinsteinVisionApi):
    def get(self, image):
        image = b64encode(image)
        req_url = '/vision/predict'
        fields = {
            'modelId': st.EINSTEIN_VISION_MODELID,
            'sampleBase64Content': image,
        }
        return self.post_requests(req_url, fields)

    def file(self, path):
        if not os.path.isfile(path):
            return None
        req_url = '/vision/predict'
        fields = {
            'modelId': st.EINSTEIN_VISION_MODELID,
            'sampleContent': ('file', open(path, 'rb'),
                              'application/octet-stream'),
        }
        return self.post_requests(req_url, fields)
