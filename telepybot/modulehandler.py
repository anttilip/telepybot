import json
from importlib import import_module

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
        self.logger = logger
        self.modules = self.get_modules()
        self.pass_args = pass_args

    def check_update(self, update):
        if isinstance(update, Update) and update.message:
            message = update.message
            try:
                module_key = message.text.split(' ', 1)[0][1:]
            except IndexError:
                return False

            return (message.text and message.text.startswith('/') and
                    module_key in self.modules.keys())
        else:
            return False

    def handle_update(self, update, dispatcher):
        optional_args = self.collect_optional_args(dispatcher)
        optional_args['logger'] = self.logger

        message = update.message or update.edited_message

        if self.pass_args:
            optional_args['args'] = message.text.split()[1:]

        try:
            # e.g. /echo testing testing!
            key, message = update.message.text.split(' ', 1)
        except ValueError:
            # e.g. /echo
            key = update.message.text

        key = key[1:]  # Remove '/' from the key
        module = self.modules[key]

        return module.handle_update(dispatcher.bot, update, **optional_args)

    def get_modules(self):
        """Loads reads json file and import found modules.
        Returns dictionaries containing the modules
        """

        module_dict = {}
        with open("modules.json", "r") as modules_json:
            module_dict = json.loads(modules_json.read())
            if self.logger:
                self.logger.info('Modules to be loaded: {}\n'.format(
                    module_dict))

        modules = {}

        for module_key in module_dict.keys():
            module_file = module_dict[module_key].split('.')[0]
            modules[module_key] = import_module('modules.' + module_file)

        return modules

    def module_summary(self):
        modules = []
        for key in self.modules:
            try:
                modules.append((key, self.modules[key].__doc__.split('\n')[0]))
            except AttributeError:
                pass
        return modules

    def get_help(self, key):
        try:
            text = self.modules[key].__doc__
            if not text:
                raise ValueError
            return text
        except (KeyError, ValueError):
            return "Couldn't find that module"
