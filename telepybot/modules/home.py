import subprocess
try:
    # Python 3+
    from configparser import ConfigParser
except ImportError:
    # Python 2
    from ConfigParser import ConfigParser

config = ConfigParser()
config.read('telepybot.conf')
allowed_users = config.get('home', 'allowedUsers').split(',')
devices_list_path = config.get('home', 'deviceListPath')
log_path = config.get('home', 'logPath')


def handle_update(bot, update, **kwargs):
    if update.message.from_user.username not in allowed_users:
        return

    command = update.message.text.lower()

    if command == '/home':
        text = show_home()
    elif command == '/home log':
        text = show_log()
    else:
        text = "Not a valid command."

    bot.sendMessage(chat_id=update.message.chat_id, text=text)


def show_home():
    devices_home = ''
    with open(devices_list_path, 'r') as home:
        devices_home = home.read()

    if devices_home == '':
        return 'No devices in network'

    return devices_home


def show_log():
    return tail(log_path, -20)


def tail(filename, n):
    proc_input = ['tail', str(n), filename]
    return subprocess.check_output(proc_input).decode('utf-8')
