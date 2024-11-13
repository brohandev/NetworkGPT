from webex_bot.models.command import Command
from ChatGPT.message_responder import handle_message


class AnswerCommand(Command):
    def __init__(self):
        super().__init__()

    def execute(self, message, attachment_actions=None, activity=None):
        """
        Process incoming message from the user, and return the text answer back to the user.

        :param message: message with command already stripped from the user
        :param attachment_actions: attachment_actions object (N.A)
        :param activity: activity object (N.A)

        :return: a string or Response object (or a list of either). Use Response if you want to return another card.
        """

        return handle_message(message)
