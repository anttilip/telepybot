"""This module echoes everything you say.
Usage:
  /echo
  /echo Hi!
Type 'cancel' to stop echoing.
"""


def handle_update(bot, update, update_queue, **kwargs):
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
