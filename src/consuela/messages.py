import json


class BotMessage(object):
    """
    A message the Consuela can send (outbound)
    """
    def __init__(self, channel, message):
        self.message = message
        self.type = 'message'
        self.channel = channel

    def get_message_with_id(self, id):
        return {
            'id': id,
            'type': self.type,
            'channel': self.channel,
            'text': self.message
        }


class Event(object):
    """
    An event from the API (inbound)
    """
    def __init__(self, data, context):
        self.raw = data
        self.context = context


class PresenceChange(Event):
    """
    An presence change from the API (inbound)
    """
    pass


class Message(Event):
    """
    A textual message from the API (inbound)
    """
    def __init__(self, data, context):
        self.text = data['text']
        self.team = data['team']
        self.type = data['type']
        self.channel = data['channel']
        self.ts = data['ts']
        self.user = data['user']
        self.raw = data
        self.context = context

    def is_own_message(self):
        return self.context['env']['self']['id'] == self.user

    def starts_with_self_mention(self):
        return self.text.startswith(self.get_own_mention())

    def get_own_mention(self):
        return "<@%s>" % self.context['env']['self']['id']


class RequestFactory(object):
    """
    Handles the creation of incoming messages
    """
    default_class = Event

    classes = {
        "message": Message,
        "presence_change": PresenceChange
    }

    @classmethod
    def create(cls, raw_data, context):

        data = json.loads(raw_data)

        try:
            return cls.classes[data['type']](data, context)
        except KeyError:
            return cls.default_class(data, context)