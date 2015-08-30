# Consuela

Consuela is a Slack chat bot that uses python's aio. Includes immediate responses
and delayed/regular tasks.


## Things to be done ASAP:

- redis persistence in scheduler
- logging
- autodiscovery plugins
- coroutines refactor
- channel context – provide it for plugins, to understand status, last responses, etc.
- Bot states. State 1: disconnected -> connected -> enable plugins coroutine -> disconnected -> disable plugins coroutine
- tests
- flake8
- setup.py
- circleci + badge
- The message server will disconnect any client that sends a message longer than 16 kilobytes. This includes all parts of the message, including JSON syntax, not just the message text. Clients should limit messages sent to channels to 4000 characters, which will always be under 16k bytes even with a message comprised solely of non-BMP Unicode characters at 4 bytes each. If the message is longer a client should prompt to split the message into multiple messages, create a snippet or create a post.
- Create's build process for autodeploy/autobuild

## Ideas:

- respond in spanish
- votes for lunches
- help command (commands in spanish too)
- Typing emulation
- When somebody mentions the bot and there is "?" in the message, the response is "No no no"
- Same as 5 but with ! there is "Me gusta"
- Use slacker's API everywhere: response = slack.users.list()
- Multiple teams. Everything is tied to a team!
- sync API calls (none at the moment) to use executors.