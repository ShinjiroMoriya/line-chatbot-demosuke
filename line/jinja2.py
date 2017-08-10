from jinja2 import Environment
from datetime import datetime


def _limit_text(value, num, dot=False):
    if len(value) > num:
        if dot:
            return value[:num] + '…'
        else:
            return value[:num]
    return value[:num]


def _filter_datetime(date, fmt='%Y-%m-%d %H:%M'):
    try:
        try:
            date = datetime.strptime(str(date), '%Y-%m-%d %H:%M:%S.%f')
        except:
            date = datetime.strptime(str(date), '%Y-%m-%d %H:%M:%S')
    except ValueError:
        try:
            date = datetime.strptime(str(date), '%Y-%m-%d')
        except:
            return ''

    return date.strftime(fmt)


def environment(**options):
    env = Environment(**options)
    env.globals.update({
    })
    env.filters.update({
        'limit_text': _limit_text,
        'datetime': _filter_datetime,
    })
    return env
