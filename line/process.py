def process_message(message):
    if message.get('type') == 'ChatMessage':
        status = 'message'
        return [status, message['message']['text']]

    elif message.get('type') == 'AgentTyping':
        pass
        # onAgentTyping()
    elif message.get('type') == 'AgentNotTyping':
        pass
        # onAgentNotTyping()
    elif message.get('type') == 'AgentDisconnect':
        pass
        # onAgentDisconnect()
    elif message.get('type') == 'ChasitorSessionData':
        pass
        # onChasitorSessionData()
    elif message.get('type') == 'ChatEnded':
        # on_endchat_message('終了しました。')
        status = 'end'
        return [status, '接続が終了しました。']
        # onChatEnded()
    elif message.get('type') == 'ChatEstablished':
        pass
        # onChatEstablished()
    elif message.get('type') == 'ChatRequestFail':
        status = 'fail'
        return [status, 'ただいま接続できません。']
    elif message.get('type') == 'ChatRequestSuccess':
        status = 'ok'
        return [status, None]
    elif message.get('type') == 'ChatTransferred':
        pass
    elif message.get('type') == 'CustomEvent':
        pass
    elif message.get('type') == 'NewVisitorBreadcrumb':
        pass
    elif message.get('type') == 'QueueUpdate':
        pass
    elif message.get('type') == 'FileTransfer':
        pass
    elif message.get('type') == 'Availability':
        pass

    return [None, None]
