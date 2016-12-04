from subprocess import check_output


def handle_update(bot, update, **kwargs):
    if not user_allowed(update.message.from_user.username):
        return

    ipv4_addr = check_output(['curl', 'v4.ifconfig.co'])
    bot.sendMessage(update.message.chat_id, text=ipv4_addr)


def user_allowed(user):
    allowed_users = []
    with open('.tmp/.ip_allowed', 'r') as f:
        allowed_users = f.read().split()

    return user in allowed_users
