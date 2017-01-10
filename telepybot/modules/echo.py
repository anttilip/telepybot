"""Echoes everything you say.

Usage:
  /echo
  /echo Hi!

Type 'cancel' to stop echoing.
"""


def handle_update(bot, update, update_queue, **kwargs):
    """Echo messages that user sends.

    This is the main function that modulehander calls.

    Args:
        bot (telegram.Bot): Telegram bot itself
        update (telegram.Update): Update that will be processed
        update_queue (Queue): Queue containing all incoming and unhandled updates
        kwargs: All unused keyword arguments. See more from python-telegram-bot
    """
    try:
        # e.g. message is "/echo I'm talking to a bot!"
        text = update.message.text.split(' ', 1)[1]
    except IndexError:
        # e.g message is just "/echo"
        text = "What do you want me to echo?"

    bot.sendMessage(chat_id=update.message.chat_id, text=text)

    # If module is more conversational, it can utilize the update_queue
    while True:
        update = update_queue.get()
        if update.message.text == "":
            text = "Couldn't echo that"
            bot.sendMessage(chat_id=update.message.chat_id, text=text)
        elif update.message.text.lower() == "cancel":
            text = "Ok, I'll stop echoing..."
            bot.sendMessage(chat_id=update.message.chat_id, text=text)
            break
        elif update.message.text.startswith('/'):
            # User accesses another bot
            update_queue.put(update)
            break
        else:
            bot.sendMessage(
                chat_id=update.message.chat_id, text=update.message.text)
