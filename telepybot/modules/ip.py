from subprocess import check_output
try:
    # Python 3+
    from configparser import ConfigParser
except ImportError:
    # Python 2
    from ConfigParser import ConfigParser

config = ConfigParser()
config.read('telepybot.conf')
allowed_users = config.get('ip', 'allowedUsers').split(',')


def handle_update(bot, update, **kwargs):
    if update.message.from_user.username not in allowed_users:
        return

    ipv4_addr = check_output(['curl', 'v4.ifconfig.co'])
    bot.sendMessage(update.message.chat_id, text=ipv4_addr)
