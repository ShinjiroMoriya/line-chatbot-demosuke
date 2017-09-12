import unicodedata
from django.views.generic import View
from django.conf import settings as st
from django.utils.html import strip_tags
from line.utilities import line_bot_api, parser
from line.logger import logger
from line.salesforce import ContactApi, FaqApi
from line.einstein_vision import Predict
from natto import MeCab
from contact.models import SfContact
from difflib import SequenceMatcher
from django.db.models import Q
from bot.models import SfBot, SfNoBot
from urllib.parse import quote
from linebot.models import (TextSendMessage,
                            TemplateSendMessage, ButtonsTemplate,
                            URITemplateAction, ConfirmTemplate,
                            PostbackTemplateAction,)


class LineCallbackView(View):
    def __init__(self, **kwargs):
        self.predict = Predict()
        self.faq = FaqApi()
        self.contact = ContactApi()
        super().__init__(**kwargs)

    @staticmethod
    def get_parts_of_speech(text):
        parts = ''
        with MeCab() as nm:
            for n in nm.parse(text, as_nodes=True):
                if not n.is_eos() and n.is_nor():
                    feature = n.feature.split(',', 1)
                    if 'SF' in feature:
                        parts = 'SF'
                    elif 'FAQ' in feature:
                        parts = 'FAQ'
                    elif '感動詞' in feature:
                        parts = '感動詞'
                    elif '名詞' in feature:
                        parts = '名詞'
        return parts

    @staticmethod
    def get_nominal_words(text):
        words = []
        with MeCab() as nm:
            for n in nm.parse(text, as_nodes=True):
                if not n.is_eos() and n.is_nor():
                    feature = n.feature.split(',', 1)
                    if 'SF' in feature:
                        words.append(n.surface)
                    elif 'FAQ' in feature:
                        words.append(n.surface)
                    elif '感動詞' in feature:
                        words.append(n.surface)
                    elif '名詞' in feature:
                        words.append(n.surface)
        return words

    @staticmethod
    def is_japanese(string):
        for ch in string:
            n = unicodedata.name(ch)
            if 'CJK UNIFIED' in n or 'HIRAGANA' in n or 'KATAKANA' in n:
                return True
        return False

    @staticmethod
    def events_parse(request):
        return parser.parse(
            request.body.decode('utf-8'),
            request.META['HTTP_X_LINE_SIGNATURE'])

    @staticmethod
    def get_session(line_id):
        session = SfContact.get_by_line_id(line_id)
        return session if session is not None else {}

    @staticmethod
    def no_reply(line_id, message):
        try:
            contact_data = SfContact.get_by_line_id(line_id)
            if contact_data is not None:
                SfNoBot.create_no_bot({
                    'contact_id': contact_data.get('sfid'),
                    'question_sentence': message,
                })
        except Exception as ex:
            logger.error(ex)
            pass

    @staticmethod
    def analysis_word(message, words):
        if len(words) == 0:
            return None

        t_queries = [Q(question__contains=t) for t in words]
        t_query = t_queries.pop()
        for item in t_queries:
            t_query |= item

        results = SfBot.objects.filter(t_query)

        results_question = {
            r.question: SequenceMatcher(
                None, message, r.question
            ).ratio() for r in results if SequenceMatcher(
                None, message, r.question
            ).ratio() > 0.4
        }

        if len(results_question) == 0:
            return None

        return max(results_question, key=(lambda x: results_question[x]))

    @staticmethod
    def new_line(text=None):
        try:
            text = strip_tags(text)
            return text.replace('<br>', '\n')
        except:
            return text

    @staticmethod
    def contact_register(event):
        line_bot_api.push_message(
            event.source.sender_id,
            TextSendMessage(
                text='下記よりユーザー登録してください。'
            )
        )
        line_client_id = st.LINE_LOGIN_CLIENT_ID
        callback_url = quote(st.URL + '/init', safe='')
        jump_url = st.LINE_LOGIN_URL.format(
            line_client_id=line_client_id,
            callback_url=callback_url)
        line_bot_api.push_message(
            event.source.sender_id,
            TemplateSendMessage(
                alt_text='ユーザー登録',
                template=ButtonsTemplate(
                    text='ユーザー登録',
                    actions=[
                        URITemplateAction(
                            label='リンク',
                            uri=jump_url
                        )
                    ]
                )
            )
        )

    def get_message_reply(self, line_id, message):
        if message == '画像リセット':
            SfContact.image_reset_by_line_id(line_id)
            return 'リセットしました。'

        if self.get_parts_of_speech(message) == '感動詞':
            return message + '\nご用件をどうぞ'

        if self.is_japanese(message) is False:
            return '日本語でお願いします。'

        words = self.get_nominal_words(message)
        results_question = self.analysis_word(message, words)

        if results_question is None:
            self.no_reply(line_id, message)
            return 'よくわかりません。'

        bot_data = SfBot.get_bot_data(results_question)
        if bot_data is None:
            return 'よくわかりません。'

        if bot_data.access_point == 'ナレッジ':
            faq_data = self.faq.get_faq(question=bot_data.references)
            if faq_data is None:
                return 'お答えすることができませんでした。'

            try:
                return bot_data.reply_sentence.format(
                    res=self.new_line(faq_data))

            except Exception as ex:
                logger.error(ex)
                return 'お答えすることができませんでした。'

        if bot_data.access_point == '顧客':
            sf_data = self.contact.get_query_by_line_id(
                query=bot_data.references,
                line_id=line_id)
            res_data = sf_data.get(bot_data.references)
            if res_data is not None:
                return bot_data.reply_sentence.format(res=res_data)

            return '情報が取得できませんでした。'

        if bot_data.access_point == 'LiveAgent':
            reply_text = bot_data.reply_sentence
            line_bot_api.push_message(
                line_id,
                TemplateSendMessage(
                    alt_text=reply_text,
                    template=ConfirmTemplate(
                        text=reply_text,
                        actions=[
                            PostbackTemplateAction(
                                label='はい',
                                data='CONNECT'
                            ),
                            PostbackTemplateAction(
                                label='いいえ',
                                data='NO_CONNECT'
                            ),
                        ]
                    )
                )
            )

    @staticmethod
    def get_predict_result(result_lists):
        result_list = result_lists[0]
        probability = result_list.get('probability', '')
        if result_list.get('probability') > 0.8:
            label = result_list.get('label')
        else:
            return '画像の認識ができませんでした。(' + str(probability) + ')'

        bot_data = SfBot.get_bot_data(label)
        if bot_data is None:
            return '画像の認識ができませんでした。(' + str(probability) + ')'

        try:
            return bot_data.reply_sentence + '\n' + '(' + str(probability) + ')'

        except Exception as ex:
            logger.error(ex)
            return '画像の認識ができませんでした。(' + str(probability) + ')'
