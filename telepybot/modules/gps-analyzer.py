"""*Handles flai.xyz route gps updates.*

This module is designed to update flai.xyz cycling routes. Update is sent as
text file containing latitude and longitude coodrinates. Days are separated
with night tag, e.g. 'n t' denotes tent night. Update is processed and pushed to
[websites assets repo](https://github.com/JaakkoLipsanen/assets/).

Usage:
```
  /gps
  > Send night type
  t
  > Send gps file
  [send gps file using telegram client]
```
"""
import os
import subprocess
import sys

import googlemaps

from telegram import ChatAction

try:
    # For Python 3.0 and later
    from urllib.parse import urlencode
    from urllib.request import URLopener
    from configparser import ConfigParser
except ImportError:
    # Fall back to Python 2's urllib
    from urllib import urlencode, URLopener
    from ConfigParser import ConfigParser

config = ConfigParser()
config.read('telepybot.conf')
api_key = config.get('gps-analyzer', 'gmapsApiKey')
routes_path = config.get('gps-analyzer', 'routesPath')
download_path = config.get('gps-analyzer', 'downloadPath')
night_type = config.get('gps-analyzer', 'defaultNightType')


def handle_update(bot, update, update_queue, **kwargs):
    """Analyze and update gps file from update.

    This is the main function that modulehander calls.

    Args:
        bot (telegram.Bot): Telegram bot itself
        update (telegram.Update): Update that will be processed
        update_queue (Queue): Queue containing all incoming and unhandled updates
        kwargs: All unused keyword arguments. See more from python-telegram-bot
    """
    chat_id = update.message.chat_id
    text = 'Send your gps file or change the night type, e.g. "h" or "t c".'
    bot.sendMessage(chat_id=chat_id, text=text)

    while True:
        update = update_queue.get()
        bot.sendChatAction(chat_id, action=ChatAction.TYPING)
        if update.message.document:
            handle_gps(bot, chat_id, update)
            break
        elif update.message.text.lower() == "cancel":
            return
        elif update.message.text.lower() == "done":
            update_only_night()
        elif update.message.text.startswith('/'):
            # User accesses another bot
            update_queue.put(update)
            break
        elif update.message.text.lower() != "":
            global night_type
            night_type = update.message.text.lower()
            text = ("Night type set to 'n {}'\nIf that is not "
                    "correct, start again by typing /'gps.'\n"
                    "Send gps file or type 'done' to send just "
                    "location.").format(night_type)
            bot.sendMessage(chat_id=chat_id, text=text)
        else:
            bot.sendMessage(
                chat_id=chat_id, text="Night type must start with 't' or 'h'")


def handle_gps(bot, chat_id, update):
    """Process the gps file and update trips route."""
    document = update.message.document

    path = download_file(update, bot.getFile(document.file_id))

    lines = []
    with open(path, 'r') as gps:
        # Splits lines to list and removes empty lines from the end
        lines = gps.read().strip().split('\n')

    file_is_valid, error_message = check_if_file_is_valid(lines)
    if not file_is_valid:
        text = 'File not valid: ' + error_message
        #pb.push_note('GPS-analyzer', text)
        bot.sendMessage(chat_id=chat_id, text=text)

    gmaps = googlemaps.Client(key=get_gmaps_API_key())
    add_elevations(lines, gmaps)
    add_night(lines)
    save_to_file(lines)

    # Commit and push changes to git
    commit_and_push()
    bot.sendMessage(chat_id=chat_id, text='Route updated.')


def download_file(update, data):
    """Downloads the gps file from update."""
    filename = update.message.document.file_name
    url = data.file_path
    file_path = os.path.join(download_path, filename)

    urlopener = URLopener()
    urlopener.retrieve(url, file_path)

    return file_path


def add_elevations(lines, gmaps):
    """Calculate altitude points for each gps coordinate."""
    for i in range(len(lines)):
        lat, lng = lines[i].split()
        result = gmaps.elevation((float(lat), float(lng)))
        elevation = int(round(result[0]['elevation']))
        lines[i] += ' ' + str(elevation)


def add_night(lines):
    """Add night in the end of gps file."""
    lines.append('n ' + night_type)
    return lines


def save_to_file(lines):
    """Append and save new gps file to trips route.txt."""
    route_path = os.path.join(routes_path, 'route.txt')
    with open(route_path, 'a') as route:
        formatted_lines = [line.strip() for line in lines]
        route.write('\n' + '\n'.join(formatted_lines))


def check_if_file_is_valid(lines):
    """Check that gps file does not have invalid syntax.

    If gps file does have invalid syntax, send line nubmer and error to user.
    """
    for i in range(len(lines)):
        try:
            # Checks if line is a coordinate pair, raises ValueError if not
            lat, lon = lines[i].split()
            float(lat)
            float(lon)
        except ValueError:
            if lines[i] == '':
                # Invalid syntax if line is empty
                return False, "Invalid syntax.\nLine {} is empty.".format(i +
                                                                          1)
            if lines[i] != 'n t' and lines[i] != 'n h':
                # Invalid syntax if line is not night location
                return False, "Invalid syntax in line {}\n'{}'".format(
                    i + 1, lines[i][:-1])
            else:
                continue
        except:
            return False, "Unhandled exception {} on line '{}'".format(
                sys.exc_info()[:2], i + 1)

    return True, None


def update_only_night():
    save_to_file(['n ' + night_type])
    commit_and_push()


def commit_and_push():
    """Commits new blog post and pushes it to github."""
    current_dir = os.getcwd()
    os.chdir(routes_path)
    subprocess.call(['git', 'pull'])
    subprocess.call(['git', 'add', '.'])
    message = '[route update]'
    subprocess.call(['git', 'commit', '-m', message])
    subprocess.call(['git', 'push'])
    os.chdir(current_dir)
