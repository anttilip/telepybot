#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging

from telegram.ext import CommandHandler, Updater
from telegram import ParseMode

from modulehandler import ModuleHandler

# Enable logging
logging.basicConfig(
    filename='.tmp/bot.log',
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO)

logger = logging.getLogger(__name__)


def start(bot, update):
    text = ("Hi!")
    bot.sendMessage(update.message.chat_id, text=text)


def help(bot, update):
    try:
        msg = update.message.text.split(' ', 1)[1]
        text = module_handler.get_help(msg)
    except IndexError:
        text = ("To find help for modules, use module name.\n"
                "For example try: /help echo\n"
                "Type /list to list all modules.")

    bot.sendMessage(update.message.chat_id, text=text, parse_mode=ParseMode.MARKDOWN)


def list(bot, update):
    modules = module_handler.module_summary()
    text = ''
    for name, description in modules:
        text += '/{} - {}\n'.format(name, description)

    bot.sendMessage(update.message.chat_id, text=text)


def reload(bot, update):
    main()
    bot.sendMessage(update.message.chat_id, text="Modules reloaded")


def error(bot, update, error):
    logger.warn('Update "%s" caused error "%s"' % (update, error))


def main():
    # Read token and create the EventHandler
    with open('auth/token.txt', 'r') as f:
        token = f.read()

    # Create the EventHandler and pass it your bot's token.
    updater = Updater(token)

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # Create ModuleHandler
    global module_handler
    module_handler = ModuleHandler(logger=logger, pass_update_queue=True)

    # on different commands - answer in Telegram
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help))
    dp.add_handler(CommandHandler("list", list))
    dp.add_handler(CommandHandler("reload", reload))
    dp.add_handler(module_handler)

    # log all errors
    dp.add_error_handler(error)

    # Start the Bot
    updater.start_polling()

    # Run the bot until the you presses Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()
