import abc


class PluginBase(abc.ABC):
    """
    A base class for all plugins
    """
    def __init__(self, publisher, scheduler):
        self.publisher = publisher
        self.scheduler = scheduler

    @abc.abstractmethod
    def is_mine(self, request):
        raise NotImplemented

    @abc.abstractmethod
    def respond(self, message):
        raise NotImplemented

    def get_help(self):
        """
        Returns help message
        :return:
        """
        return "No help message for this command available"