from telegram import Update
from telegram.ext import Handler


class ModuleHandler(Handler):
    def __init__(self,
                 logger=None,
                 pass_args=False,
                 pass_update_queue=False,
                 pass_job_queue=False):

        super(ModuleHandler, self).__init__(
            None,
            pass_update_queue=pass_update_queue,
            pass_job_queue=pass_job_queue)
        self.pass_args = pass_args

    def check_update(self, update):
        if isinstance(update, Update) and update.message:
            message = update.message
            # TODO: If message.text is directed to modules, return True
            if message.text == "/module":
                return True
        else:
            return False

    def handle_update(self, update, dispatcher):
        optional_args = self.collect_optional_args(dispatcher)

        message = update.message or update.edited_message

        # TODO: Send update to modules
        dispatcher.bot.sendMessage(
            update.message.chat_id,
            'I got your message but do not know how to reply')

    def get_modules(self):
        """Loads reads json file and import found modules.
        Returns dictionaries containing the modules
        """
        # TODO: Implement
        raise NotImplementedError
