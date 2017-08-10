import sys
import os
import dj_database_url
from datetime import timedelta

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
SECRET_KEY = os.environ.get('SECRET_KEY', 'test')
DEBUG = os.environ.get('DEBUG', None) == 'True'
LOCAL = os.environ.get('LOCAL', None) == 'True'
TESTING = len(sys.argv) > 1 and sys.argv[1] == 'test'
DEV = os.environ.get('DEV', None) == 'True'
ALLOWED_HOSTS = [os.environ.get('HOST', '*')]
SECURE_SSL_REDIRECT = os.environ.get('SSL', None) == 'True'
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
LANGUAGE_CODE = 'ja'
TIME_ZONE = 'Asia/Tokyo'
USE_I18N = True
USE_L10N = True
USE_TZ = False
LIVEAGENT_API_URL = os.environ.get('LIVEAGENT_API_URL')
ROOT_URLCONF = 'line.urls'
WSGI_APPLICATION = 'line.wsgi.application'
API_VERSION = str(os.environ.get('API_VERSION', 40))
LIVEAGENT_HOST = os.environ.get('LIVEAGENT_HOST')
LIVEAGENT_ORGANIZATION_ID = os.environ.get('LIVEAGENT_ORGANIZATION_ID')
LIVEAGENT_DEPLOYMENT_ID = os.environ.get('LIVEAGENT_DEPLOYMENT_ID')
LIVEAGENT_BUTTON_ID = os.environ.get('LIVEAGENT_BUTTON_ID')
USER_AGENT = os.environ.get('USER_AGENT', 'Mozilla/5.0')
LINE_ACCESS_TOKEN = os.environ.get('LINE_ACCESS_TOKEN')
LINE_ACCESS_SECRET = os.environ.get('LINE_ACCESS_SECRET')
LINE_LOGIN_CLIENT_ID = os.environ.get('LINE_LOGIN_CLIENT_ID')
LINE_LOGIN_SECRET_ID = os.environ.get('LINE_LOGIN_SECRET_ID')
URL = os.environ.get('URL', 'localhost:8000')

if DEBUG:
    INTERNAL_IPS = ('127.0.0.1',)

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_rq',
    'dictionary',
    'contact',
    'app',
    'bot',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.jinja2.Jinja2',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'environment': 'line.jinja2.environment',
        },
    },
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': ['templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.contrib.auth.context_processors.auth',
            ],
        },
    },
]

if TESTING:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
        }
    }
else:
    db = dj_database_url.parse(os.environ.get('DATABASE_URL') +
                               '?currentSchema=salesforce,public')
    try:
        del db['OPTIONS']['currentSchema']
    except:
        pass

    DATABASES = {
        'default': db
    }

LOGGING = {
    'version': 1,
    'formatters': {
        'all': {
            'format': '\t'.join([
                '[%(levelname)s]',
                'code:%(lineno)s',
                'asctime:%(asctime)s',
                'module:%(module)s',
                'message:%(message)s',
            ])
        },
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'all'
        },
    },
    'loggers': {
        'command': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
    },
}

STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATIC_URL = '/static/'
STATICFILES_DIRS = (os.path.join(BASE_DIR, 'static'),)
STATICFILES_STORAGE = 'whitenoise.django.GzipManifestStaticFilesStorage'

SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_COOKIE_AGE = timedelta(days=30).total_seconds()
SESSION_SAVE_EVERY_REQUEST = True

MESSAGE_STORAGE = 'django.contrib.messages.storage.cookie.CookieStorage'

if DEBUG is None:
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': os.environ.get('REDIS_URL', 'redis://127.0.0.1:6379'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}

RQ_QUEUES = {
    'default': {
        'USE_REDIS_CACHE': 'default',
    },
    'high': {
        'USE_REDIS_CACHE': 'default',
    },
    'low': {
        'USE_REDIS_CACHE': 'default',
    },
}

PASSWORD_HASHERS = (
    'django.contrib.auth.hashers.BCryptPasswordHasher',
)
