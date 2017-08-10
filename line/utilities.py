from django.conf import settings as st
from linebot import LineBotApi, WebhookParser
from line.logger import logger


line_bot_api = LineBotApi(st.LINE_ACCESS_TOKEN)
parser = WebhookParser(st.LINE_ACCESS_SECRET)


def get_profile(line_id):
    try:
        return line_bot_api.get_profile(line_id)
    except Exception as e:
        logger.info(e)
        return {}
