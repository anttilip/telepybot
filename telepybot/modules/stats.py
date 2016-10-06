"""Returns bots ping, uptime and current load.
"""
from datetime import datetime
from math import ceil
from subprocess import check_output


def handle_update(bot, update, **kwargs):
    sent_time = update.message.date
    now = datetime.now()
    delta = now - sent_time

    ping = ceil(delta.total_seconds() * 1000)
    uptime = check_output(['uptime', '-p']).decode().split(' ', 1)[1]

    output = check_output(['cat', '/proc/loadavg']).split()[1].decode()
    load_5m = float(output) * 100

    report = ("Ping: {}ms\nBot uptime: {}"
              "Load over last 5 minutes: {}%").format(ping, uptime, load_5m)

    bot.sendMessage(update.message.chat_id, text=report)
