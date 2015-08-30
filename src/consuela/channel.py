import json
import asyncio

import logging

import aiohttp

from consuela.messages import RequestFactory


MAX_CONNECT_RETRIES = 5
CONNECT_RETRY_TIME = 5

logger = logging.getLogger(__name__)


class ConnectionDroppedException(Exception):
    pass


class Channel(object):
    """
    This class is responsible only for the communication between a client and a server
    It doesn't know anything about plugins. Just gets messages and sends messages
    """
    def __init__(self, slack):
        self.slack = slack
        self.ws = None
        self.message_counter = 0
        self.env = {}
        self.message_callback = None

    @asyncio.coroutine
    def run(self):

        @asyncio.coroutine
        def runner():

            self._rtm_prepare()

            self.ws = yield from aiohttp.ws_connect(self.env['url'])

            while True:
                raw_data = yield from self.ws.receive()

                if raw_data.tp in (aiohttp.MsgType.closed, aiohttp.MsgType.error):
                    raise ConnectionDroppedException()

                context = {
                    'env': self.env
                }

                request = RequestFactory.create(raw_data.data, context)

                outbound_message = self.message_callback(request)

                if outbound_message:
                    yield from self.send_message(outbound_message)

        retries = 0

        while True:
            try:
                yield from runner()
                retries = 0
            except ConnectionDroppedException:
                logger.info("Retrying to connect: {retries}".format(retries=retries))
                yield from asyncio.sleep(CONNECT_RETRY_TIME)
                retries += 1

            if retries == MAX_CONNECT_RETRIES:
                logger.info("Max number of retries reached: {retries}".format(retries=retries))
                break

    def set_message_callback(self, callback):
        self.message_callback = callback

    def get_publisher(self):

        def publisher(message):
            yield from self.send_message(message)

        return publisher

    @asyncio.coroutine
    def send_message(self, outbound_message):
        self.message_counter += 1
        data = outbound_message.get_message_with_id(self.message_counter)

        data_str = json.dumps(data)

        self.ws.send_str(data_str)

    def _rtm_prepare(self):
        res = self.slack.rtm.start()

        if not res.successful:
            raise Exception("Unable to initiate the session")

        self.env = res.body
