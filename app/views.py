import sys
from base64 import b64encode
from django.views.generic import View
from django.shortcuts import redirect, render
from django.contrib import messages
from django.http import HttpResponse, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from line.utilities import line_bot_api
from line.logger import logger
from line.line_api import get_line_id
from line.forms import RegisterForm
from line.service import get_error_message, session_delete
from line.liveagent import send_message, connect_liveagent, get_messages
from contact.models import SfContact, CountException
from line.line_view import LineCallbackView
from linebot.models import (MessageEvent, TextSendMessage, FollowEvent,
                            PostbackEvent)


class CallbackView(LineCallbackView):
    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    @staticmethod
    def get(_):
        return HttpResponse()

    def post(self, request):
        try:
            events = self.events_parse(request)

        except Exception as ex:
            logger.error(ex)
            return HttpResponseForbidden()

        for event in events:
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
                session = self.get_session(line_id)
                if session is None:
                    self.contact_register(event)
                    return HttpResponse()

                if event.message.type == 'text':

                    message = event.message.text

                    if session.get('responder') == 'LIVEAGENT':
                        res = send_message(line_id, message)
                        if res is False:
                            line_bot_api.reply_message(
                                event.reply_token,
                                TextSendMessage(
                                    text='恐れ入りますが、もう一度送ってください。'
                                )
                            )
                    else:
                        reply_text = self.get_message_reply(
                            line_id, message)

                        line_bot_api.reply_message(
                            event.reply_token,
                            TextSendMessage(
                                text=reply_text
                            )
                        )

                if event.message.type == 'image':
                    if session.get('responder') != 'LIVEAGENT':
                        message_content = line_bot_api.get_message_content(
                            event.message.id)
                        try:
                            SfContact.image_upload_by_line_id(
                                line_id,
                                message_content.content,
                                event.message.id)
                            result = self.predict.base64(
                                b64encode(message_content.content))
                            reply_text = self.get_predict_result(
                                result.get('probabilities'))
                            line_bot_api.reply_message(
                                event.reply_token,
                                TextSendMessage(
                                    text=reply_text
                                )
                            )

                        except:
                            return HttpResponse()

        return HttpResponse()


class ContactInit(View):
    @staticmethod
    def get(request):
        code = request.GET.get('code')
        if code is None:
            return HttpResponse()
        line_id = get_line_id(code)
        request.session['line_id'] = line_id
        return redirect('/register')


class ContactRegister(View):
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


class ContactRegisterComplete(View):
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
