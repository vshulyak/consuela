import asyncio
import os
import logging

from slacker import Slacker

from consuela.channel import Channel
from consuela.scheduler import Scheduler

from consuela.plugins.hola import HolaPlugin
from consuela.plugins.no_command_found import NoCommandFoundPlugin
from consuela.plugins.remind import RemindPlugin


logger = logging.getLogger('websockets.server')
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler())


class BotPluginRunner(object):
    """
    Handler for passing messages from the slack api to plugins
    """
    def __init__(self, channel, scheduler):
        self.channel = channel
        self.scheduler = scheduler
        self.message_counter = 0
        self.plugins = []

        channel.set_message_callback(self.handle_request)

    def register_plugin(self, plugin_class):
        handler = plugin_class(self.channel.get_publisher(), self.scheduler)
        self.plugins.append(handler)

    def handle_request(self, request):

        for plugin in self.plugins:

            # try catch
            if plugin.is_mine(request):

                # try catch
                asyncio.async(plugin.respond(request))

                # for now there is no need to let multiple plugins
                # handle requests
                break


def main():

    # kind of a hack for now
    os.environ['TZ'] = 'Europe/Moscow'

    slack = Slacker(os.environ['SLACK_API_KEY'])
    channel = Channel(slack)
    scheduler = Scheduler()

    bot_runner = BotPluginRunner(channel=channel, scheduler=scheduler)

    # in future, there should be autodiscovery used for this
    bot_runner.register_plugin(RemindPlugin)
    bot_runner.register_plugin(HolaPlugin)
    bot_runner.register_plugin(NoCommandFoundPlugin)

    loop = asyncio.get_event_loop()

    while True:
        asyncio.async(scheduler.run())
        asyncio.async(channel.run())
        loop.run_forever()

    loop.close()