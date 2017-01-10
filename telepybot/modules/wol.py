from subprocess import call
try:
    # Python 3+
    from configparser import ConfigParser
except ImportError:
    # Python 2
    from ConfigParser import ConfigParser

config = ConfigParser()
config.read('telepybot.conf')
allowed_users = config.get('wol', 'allowedUsers').split(',')
mac_addr = config.get('wol', 'macAddress')
host_name = config.get('wol', 'hostName')


def handle_update(bot, update, **kwargs):
    if update.message.from_user.username not in allowed_users:
        return

    call(['sudo', 'etherwake', mac_addr])
    text = "WOL package sent to " + host_name
    bot.sendMessage(update.message.chat_id, text=text)
