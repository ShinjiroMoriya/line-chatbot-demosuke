import sys
from django.views.generic import View
from django.shortcuts import redirect, render
from django.contrib import messages
from django.http import HttpResponse, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.conf import settings as st
from django.utils.html import strip_tags
from line.utilities import line_bot_api, parser
from line.logger import logger
from line.liveagent import connect_liveagent, get_messages, send_message
from line.line_api import get_line_id
from line.forms import RegisterForm
from line.service import get_error_message, session_delete
from line.salesforce import ContactApi, FaqApi
from natto import MeCab
from contact.models import SfContact
from difflib import SequenceMatcher
from django.db.models import Q
from bot.models import SfBot, SfNoBot
from app.models import LineSession
from urllib.parse import quote
from linebot.models import (MessageEvent, TextSendMessage,
                            TemplateSendMessage, ButtonsTemplate,
                            PostbackEvent, URITemplateAction,
                            PostbackTemplateAction, ConfirmTemplate,
                            FollowEvent)


class CallbackView(View):
    def __init__(self, **kwargs):
        self.url = st.LIVEAGENT_API_URL
        self.faq = FaqApi()
        self.contact = ContactApi()
        super().__init__(**kwargs)

    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

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
    def events_parse(request):
        return parser.parse(
            request.body.decode('utf-8'),
            request.META['HTTP_X_LINE_SIGNATURE'])

    @staticmethod
    def get_session(line_id):
        session = LineSession.get_by_line(line_id)
        return session if session is not None else {}

    @staticmethod
    def no_reply(event):
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text='よくわかりません')
        )
        try:
            contact_data = SfContact.get_by_line_id(event.source.sender_id)
            if contact_data is not None:
                SfNoBot.create_no_bot({
                    'contact_id': contact_data.get('sfid'),
                    'question_sentence': event.message.text,
                })
        except Exception as ex:
            logger.error(ex)
            pass

    @staticmethod
    def analysis_word(message, words):
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

        jump_url = ('https://access.line.me/dialog/oauth/'
                    'weblogin?response_type=code&client_id'
                    '=' + line_client_id + '&redirect_uri=' +
                    callback_url +
                    '&state=register')
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

    @staticmethod
    def get(_):
        return HttpResponse()

    def post(self, request):
        try:
            events = self.events_parse(request)

        except Exception as ex:
            logger.error(ex)
            return HttpResponseForbidden()

        event = events[0]
        line_id = event.source.sender_id

        if isinstance(event, FollowEvent):
            self.contact_register(event)

        if isinstance(event, PostbackEvent):
            if event.postback.data == 'CONNECT':
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(
                        text='お繋ぎしますので少々お待ちください。'
                    )
                )
                is_connect = connect_liveagent(line_id)
                if is_connect is True:
                    get_messages.delay(line_id)

                else:
                    line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage(
                            text=('担当者が席をはずしておりますので、'
                                  '時間をあけて再度お呼び出しください。')
                        )
                    )
            elif event.postback.data == 'NO_CONNECT':
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(
                        text=('かしこまりました。何かあればメニューから'
                              'オペレーターを呼出してください。')
                    )
                )

        if isinstance(event, MessageEvent):
            message = event.message.text
            session = self.get_session(line_id)

            contact_data = SfContact.get_by_line_id(line_id)
            if contact_data is None:
                self.contact_register(event)
                return HttpResponse()

            if session.get('responder') == 'LIVEAGENT':
                res = send_message(line_id, message)
                if res is False:
                    line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage(
                            text='恐れ入りますが、もう一度送ってください。'
                        )
                    )

                return HttpResponse()

            if self.get_parts_of_speech(message) == '感動詞':
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(
                        text=message + ' ご用件をどうぞ'
                    )
                )
                return HttpResponse()

            words = self.get_nominal_words(message)
            results_question = self.analysis_word(message, words)

            if results_question is None:
                self.no_reply(event)
                return HttpResponse()

            bot_data = SfBot.get_bot_data(results_question)
            if bot_data is None:
                return HttpResponse()

            if bot_data.access_point == 'ナレッジ':
                faq_data = self.faq.get_faq(question=bot_data.references)
                if faq_data is None:
                    line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage(
                            text='お答えすることができませんでした。'
                        )
                    )

                else:
                    try:
                        line_bot_api.reply_message(
                            event.reply_token,
                            TextSendMessage(
                                text=bot_data.reply_sentence.format(
                                    res=self.new_line(faq_data))
                            )
                        )
                    except Exception as ex:
                        logger.error(ex)
                        pass

            elif bot_data.access_point == 'LiveAgent':
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
            else:
                sf_data = self.contact.get_query_by_line_id(
                    query=bot_data.references,
                    line_id=line_id)
                res_data = sf_data.get(bot_data.references)
                if res_data is not None:
                    repry_text = bot_data.reply_sentence.format(
                        res=res_data)
                else:
                    repry_text = '情報が取得できませんでした。'

                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(
                        text=repry_text
                    )
                )

        return HttpResponse()


class LiveagentInit(View):
    @staticmethod
    def get(request):
        code = request.GET.get('code')
        if code is None:
            return HttpResponse()
        line_id = get_line_id(code)
        request.session['line_id'] = line_id
        return redirect('/register')


class LiveagentRegister(View):
    def __init__(self, **kwargs):
        self.data = {}
        self.request_data = {}
        self.error_messages = {}
        self.form_data = {}
        super().__init__(**kwargs)

    def dispatch(self, request, *args, **kwargs):
        if request.method == 'GET':
            self.request_data = request.session.get('request_data')
            self.error_messages = request.session.get('error_messages')
            self.form_data = request.session.get('form_data')
            self.data = {
                'request_data': self.request_data,
                'form_data': self.form_data,
                'messages': self.error_messages,
            }
        return super().dispatch(request, *args, **kwargs)

    def get(self, request):
        line_id = request.session.get('line_id')
        if line_id is None:
            return HttpResponseForbidden()

        self.data.update({
            'line_id': line_id,
        })
        contact_data = SfContact.get_by_line_id(line_id)
        if contact_data is not None:
            self.data.update({
                'registered': True
            })

        return render(request, 'register.html', {'data': self.data})

    @staticmethod
    def post(request):

        form = RegisterForm(request.POST)

        if form.errors:
            messages.add_message(request, messages.INFO,
                                 dict(form.errors.items()))

        if form.is_valid():
            session_delete(request, ['form_data'])
            line_id = form.cleaned_data.get('line_id')
            email = form.cleaned_data.get('email')

            contact_data = SfContact.get_obj_by_email(email)
            if len(contact_data) == 0:
                request.session['request_data'] = {
                    'status': 'SF_DOES_NOT_DATA',
                }
                request.session['form_data'] = form.cleaned_data
                request.session['error_messages'] = get_error_message(request)

                return redirect('/register')
            else:
                contact_data.update(line_id=line_id)

            return redirect('/register/complete')

        else:
            request.session['form_data'] = form.cleaned_data
            request.session['error_messages'] = get_error_message(request)

            return redirect('/register')


class LiveagentRegisterComplete(View):
    @staticmethod
    def get(request):
        session_delete(request, ['request_data', 'form_data',
                                 'error_messages', 'line_id'])
        return render(request, 'register-complete.html', {})


class AppricationError(View):
    @staticmethod
    def get(_):
        try:
            logger.error(sys.exc_info())
        except:
            pass
        return HttpResponse()
