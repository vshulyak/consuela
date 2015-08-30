import asyncio

from consuela.messages import BotMessage, Message

from consuela.plugins import PluginBase


class HolaPlugin(PluginBase):
    """
    Says Hola if someone says hola
    """
    def is_mine(self, request):
        return isinstance(request, Message)\
               and not request.is_own_message() \
               and request.starts_with_self_mention()\
               and request.type == 'message' \
               and "hola" in request.text.lower()

    @asyncio.coroutine
    def respond(self, request):
        response = BotMessage(request.channel, "¡Hola!")
        yield from self.publisher(response)