import asyncio
import random

from consuela.messages import BotMessage, Message

from consuela.plugins import PluginBase


responses = ("No te entiendo", "Es buen tiempo en México", "Housekeeping...")


class NoCommandFoundPlugin(PluginBase):
    """
    Responds with a random phrase

    Should be registered last to handle situations when Consuela
    doesn't know anything about the command a user passed
    """
    def is_mine(self, request):
        return isinstance(request, Message)\
               and not request.is_own_message()\
               and request.starts_with_self_mention()

    @asyncio.coroutine
    def respond(self, request):
        response = BotMessage(request.channel,
                              responses[random.randint(0, len(responses)-1)])
        yield from self.publisher(response)
