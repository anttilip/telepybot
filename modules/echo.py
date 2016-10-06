def handle_update(bot, update):
    try:
        # e.g. message is "/echo I'm talking to a bot!"
        text = update.message.text.split(' ', 1)[1]
    except IndexError:
        # e.g message is just "/echo"
        text = "I can't echo that"

    bot.sendMessage(chat_id=update.message.chat_id, text=text)
