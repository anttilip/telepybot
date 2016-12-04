from subprocess import call


def handle_update(bot, update, **kwargs):
    if not user_allowed(update.message.from_user.username):
        return

    call(['sudo', 'etherwake', '30:5a:3a:df:ca:62'])
    text = "WOL package sent to redmond"
    bot.sendMessage(update.message.chat_id, text=text)


def user_allowed(user):
    allowed_users = []
    with open('.tmp/.wol_allowed', 'r') as f:
        allowed_users = f.read().split()

    return user in allowed_users
