import subprocess


def handle_update(bot, update, **kwargs):
    if not user_allowed(update.message.from_user.username):
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
    with open('.tmp/CurrentlyInNetwork.txt', 'r') as home:
        devices_home = home.read()

    if devices_home == '':
        return 'No devices in network'

    return devices_home


def show_log():
    return tail('.tmp/maclog.txt', -20)


def tail(filename, n):
    proc_input = ['tail', str(n), filename]
    return subprocess.check_output(proc_input).decode('utf-8')


def user_allowed(user):
    allowed_users = []
    with open('.tmp/.home_allowed', 'r') as f:
        allowed_users = f.read().split()

    return user in allowed_users
