import requests
import json
from django.conf import settings


def get_access_token(code):
    url = 'https://api.line.me/v1/oauth/accessToken'
    post_data = {
        'grant_type': 'authorization_code',
        'client_id': settings.LINE_LOGIN_CLIENT_ID,
        'client_secret': settings.LINE_LOGIN_SECRET_ID,
        'code': code,
        'redirect_uri': '',
    }
    r = requests.post(url, post_data)
    result = json.loads(r.text)
    return result.get('access_token')


def get_line_id(code):
    access_token = get_access_token(code)
    url = 'https://api.line.me/v2/profile'
    headers = {
        'Authorization': 'Bearer ' + access_token
    }
    r = requests.get(url, headers=headers)
    result = json.loads(r.text)
    return result.get('userId')
