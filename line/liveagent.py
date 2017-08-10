import requests
import json
from django.conf import settings as st
from app.models import LineSession
from line.utilities import get_profile, line_bot_api
from django_rq import job
from line.logger import logger
from line.process import process_message
from linebot.models import TextSendMessage


def get_liveagent_session(line_id):
    session_obj = LineSession.get_by_line(line_id=line_id)
    if session_obj is None:
        url = st.LIVEAGENT_HOST + '/chat/rest/System/SessionId'
        headers = {
            'X-LIVEAGENT-API-VERSION': st.API_VERSION,
            'X-LIVEAGENT-AFFINITY': 'null',
        }
        r = requests.get(url, headers=headers)
        if r.status_code == 200:
            res_data = json.loads(r.text)
            res_data.update({
                'line_id': line_id,
                'sequence': 1,
            })
            try:
                return LineSession.save_session(res_data)
            except:
                pass

    elif session_obj.get('key') is None:
        url = st.LIVEAGENT_HOST + '/chat/rest/System/SessionId'
        headers = {
            'X-LIVEAGENT-API-VERSION': st.API_VERSION,
            'X-LIVEAGENT-AFFINITY': 'null',
        }
        r = requests.get(url, headers=headers)
        if r.status_code == 200:
            res_data = json.loads(r.text)
            update_data = {
                'line_id': line_id,
                'key': res_data.get('key'),
                'affinity_token': res_data.get('affinityToken'),
            }
            try:
                return LineSession.update_session(update_data)
            except:
                pass

    return session_obj


def connect_liveagent(line_id):
    session = get_liveagent_session(line_id)
    profile = get_profile(line_id)
    url = st.LIVEAGENT_HOST + '/chat/rest/Chasitor/ChasitorInit'
    headers = {
        'X-LIVEAGENT-API-VERSION': st.API_VERSION,
        'X-LIVEAGENT-AFFINITY': session.get('affinity_token'),
        'X-LIVEAGENT-SESSION-KEY': session.get('key'),
        'X-LIVEAGENT-SEQUENCE': str(session.get('sequence')),
    }
    post_data = {
        'organizationId': st.LIVEAGENT_ORGANIZATION_ID,
        'deploymentId': st.LIVEAGENT_DEPLOYMENT_ID,
        'buttonId': st.LIVEAGENT_BUTTON_ID,
        'sessionId': session.get('liveagent_id'),
        'userAgent': st.USER_AGENT,
        'language': 'ja',
        'trackingId': '',
        'screenResolution': '',
        'visitorName': profile.display_name,
        'isPost': True,
        'receiveQueueUpdates': True,
        'buttonOverrides': [],
        'prechatDetails': [
            {
                'label': 'ContactLineId',
                'value': session.get('line_id'),
                'entityMaps': [],
                'transcriptFields': [],
                'displayToAgent': True,
                'doKnowledgeSearch': False
            },
        ],
        'prechatEntities': [
            {
                'entityName': 'Contact',
                'showOnCreate': False,
                'linkToEntityName': None,
                'linkToEntityField': None,
                'saveToTranscript': 'ContactId',
                'entityFieldsMaps': [
                    {
                        'fieldName': 'LINE_ID__c',
                        'label': 'ContactLineId',
                        'doFind': True,
                        'isExactMatch': True,
                        'doCreate': False,
                    }
                ]
            }
        ],
    }
    r = requests.post(url, json=post_data, headers=headers)
    if r.status_code == 200:
        LineSession.update_session({
            'line_id': line_id,
            'sequence': str(session.get('sequence') + 1),
        })
        url = st.LIVEAGENT_HOST + '/chat/rest/System/Messages'
        headers = {
            'X-LIVEAGENT-API-VERSION': st.API_VERSION,
            'X-LIVEAGENT-AFFINITY': session.get('affinity_token'),
            'X-LIVEAGENT-SESSION-KEY': session.get('key'),
        }
        r = requests.get(url, headers=headers, params={
            'ack': session.get('ack', -1)
        })
        try:
            result = None
            res_type = None
            if r.status_code == 200:
                body = json.loads(r.text)
                for message in body.get('messages'):
                    res_type, result = process_message(message)

                if res_type == 'end' or res_type == 'fail':
                    LineSession.delete_session(line_id)
                    if result is not None:
                        line_bot_api.push_message(
                            line_id,
                            TextSendMessage(
                                text=result
                            )
                        )

                else:
                    LineSession.update_session({
                        'line_id': line_id,
                        'ack': body.get('sequence'),
                        'responder': 'LIVEAGENT',
                    })

            elif r.status_code == 204:
                LineSession.delete_session(line_id)

            return True

        except Exception as ex:
            logger.info(ex)
            return False

    else:
        LineSession.delete_session(line_id)
        return False


@job('high', timeout=1000)
def get_messages(line_id):
    session = LineSession.get_by_line(line_id=line_id)
    if session is None:
        return ['bad', 'bad request']

    url = st.LIVEAGENT_HOST + '/chat/rest/System/Messages'
    headers = {
        'X-LIVEAGENT-API-VERSION': st.API_VERSION,
        'X-LIVEAGENT-AFFINITY': session.get('affinity_token'),
        'X-LIVEAGENT-SESSION-KEY': session.get('key'),
    }
    r = requests.get(url, headers=headers, params={
        'ack': session.get('ack', -1)
    })
    try:
        res_type = None
        result = None
        if r.status_code == 200:
            body = json.loads(r.text)
            for message in body.get('messages'):
                res_type, result = process_message(message)

            if res_type == 'end' or res_type == 'fail':
                LineSession.delete_session(line_id)
            else:
                LineSession.update_session({
                    'line_id': line_id,
                    'ack': body.get('sequence'),
                })

            if result is not None:
                line_bot_api.push_message(
                    line_id,
                    TextSendMessage(
                        text=result
                    )
                )

            get_messages(line_id)

        elif r.status_code == 204:
            get_messages(line_id)

    except Exception as ex:
        logger.info(ex)
        LineSession.delete_session(line_id=line_id)
        pass


def send_message(line_id, message):
    session = LineSession.get_by_line(line_id=line_id)
    url = st.LIVEAGENT_HOST + '/chat/rest/Chasitor/ChatMessage'
    headers = {
        'X-LIVEAGENT-API-VERSION': st.API_VERSION,
        'X-LIVEAGENT-AFFINITY': session.get('affinity_token'),
        'X-LIVEAGENT-SESSION-KEY': session.get('key'),
        'X-LIVEAGENT-SEQUENCE': str(session.get('sequence')),
    }
    post_data = {
        'text': message
    }
    r = requests.post(url, json=post_data, headers=headers)
    if r.status_code == 200:
        LineSession.update_session({
            'line_id': line_id,
            'sequence': session.get('sequence') + 1,
        })
        return True
    else:
        LineSession.delete_session(line_id)
        return False
