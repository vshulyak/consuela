import asyncio
import parsedatetime
import humanize

from datetime import datetime
from time import mktime

from parse import parse, with_pattern

from consuela.messages import Message, BotMessage

from consuela.plugins import PluginBase

from consuela.scheduler import RunAtDateTimeTask


ME_ALIASES = ["me"]

cal = parsedatetime.Calendar()


class InvalidFormatException(Exception):

    def __init__(self, message, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.message = message


class InvalidUserException(InvalidFormatException):
    pass


class InvalidTimeException(InvalidFormatException):
    pass


class RemindTask(RunAtDateTimeTask):
    """
    A task that actually reminds
    """
    def __init__(self, run_at, publisher, original_message, whom_list, action_text):
        super(RemindTask, self).__init__(run_at, publisher)
        self.whom_list = whom_list
        self.original_message = original_message
        self.created = datetime.now()
        self.action_text = action_text

    def __str__(self):
        return "Remind task with message: {message}"\
            .format(message=self.original_message)

    @asyncio.coroutine
    def run(self):
        print("run remind")

        response = BotMessage(self.original_message.channel, "You asked me to remind {whom} to {action}".format(
            whom=", ".join(self.whom_list),
            action=self.action_text
        ))

        yield from self.publisher(response)


class RemindPlugin(PluginBase):
    """
    Used for messages starting with a particular predefined command
    """
    def is_mine(self, request):

        return isinstance(request, Message) \
               and not request.is_own_message() \
               and (request.text.startswith("%s remind " % request.get_own_mention()) or \
                    request.text.startswith("%s: remind " % request.get_own_mention()))
               # TODO: this is awkward, messages should come as a class containing command info in advance
               # since we have fixed format of commands: @consuela <command> (can be parsed)

    @asyncio.coroutine
    def respond(self, message):

        @with_pattern(r"in|at")
        def parse_type(text):
            return text

        # todo: should be handled in message class
        text = message.text.replace(message.get_own_mention(), '', 1)

        if text.startswith(":"):
            text = text.replace(":", "", 1)
        text = text.strip()

        pattern = "remind {whom} {type:type} {when} to {action}"
        res = parse(pattern, text, dict(type=parse_type))

        if not res:
            response = BotMessage(message.channel, "the pattern is: %s" % pattern)
            yield from self.publisher.send_response(response)
            return

        time_struct, parse_status = cal.parse(res['when'])
        run_at = datetime.fromtimestamp(mktime(time_struct))

        try:
            whom_list = self.parse_users(message, res['whom'])
        except InvalidUserException as e:
            response = BotMessage(message.channel, "Perdóname, mas: %s" % e.message)
            yield from self.publisher.send_response(response)
            return

        # todo: if not time

        if res['type'] == "in":
            when_readable = "%s, %s" % (humanize.naturalday(run_at), humanize.naturaltime(run_at))
        else:
            when_readable = "%s, %s" % (humanize.naturalday(run_at), run_at.time())

        # register the delayed task
        task = RemindTask(run_at, self.publisher, message, whom_list, res['action'])
        self.scheduler.register_task(task)

        # immediate response
        response = BotMessage(message.channel,
                               "Ok, will remind _{whom}_ *{when_readable}* "
                               "to _{action}_".format(whom=", ".join(whom_list),
                                                      when_readable=when_readable,
                                                      action=res['action']))

        yield from self.publisher(response)

    def parse_users(self, message, whom):

        nicknames = []

        for user in {item.strip() for item in whom.split(",")}:
            if user in ME_ALIASES:
                nicknames.append("<@%s>" % message.user)
            elif parse("<@{name}>", user):
                nicknames.append(user)
            else:
                raise InvalidUserException("{nickname} does not exist in our team".format(nickname=user))

        return nicknames