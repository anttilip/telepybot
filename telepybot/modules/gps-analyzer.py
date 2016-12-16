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
from telegram import ChatAction
import os
import sys
import subprocess
try:
    # For Python 3.0 and later
    from urllib.parse import urlencode
    from urllib.request import URLopener
except ImportError:
    # Fall back to Python 2's urllib2
    from urllib2 import urlencode, URLopener

if os.path.exists('/home/pi/Projects/flai.xyz/assets'):
    # raspberry pi
    routes_path = os.path.abspath(
        '/home/pi/Projects/flai.xyz/assets/cycle/routes/israel&jordan2016')
    download_path = os.path.abspath(
        '/home/pi/Projects/telepybot/telepybot/.downloads')
elif os.path.exists('C:/Users/alips/Projects/flai.xyz/assets'):
    # home windows 10 desktop
    routes_path = os.path.abspath(
        'C:/Users/alips/Projects/flai.xyz/assets/cycle/routes/israel&jordan2016')
    download_path = os.path.abspath(
        'C:/Users/alips/Projects/telepybot/telepybot/.downloads')
elif os.path.exists('/mnt/c/Users/alips/Projects/flai.xyz/assets'):
    # home windows 10 desktop
    routes_path = os.path.abspath(
        '/mnt/c/Users/alips/Projects/flai.xyz/assets/cycle/routes/israel&jordan2016')
    download_path = os.path.abspath(
        '/mnt/c/Users/alips/Projects/telepybot/telepybot/.downloads')
else:
    print("No valid assets folder found.")
    raise OSError

# Default night type is 't' as in tent
night_type = 't'


def handle_update(bot, update, update_queue, **kwargs):
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
        elif update.message.text.lower() != "":
            global night_type
            night_type = update.message.text.lower()
            text = ("Night type set to 'n {}'\nIf that is not "
                    "correct, start again by typing /'gps.'\n"
                    "Send gps file or type 'done' to send just "
                    "location.").format(night_type)
            bot.sendMessage(chat_id=chat_id, text=text)
        elif update.message.text.startswith('/'):
            # User accesses another bot
            update_queue.put(update)
            break
        else:
            bot.sendMessage(
                chat_id=chat_id, text="Night type must start with 't' or 'h'")


def handle_gps(bot, chat_id, update):
    print('asd')
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

    add_night(lines)
    save_to_file(lines)

    # Commit and push changes to git
    commit_and_push()
    bot.sendMessage(chat_id=chat_id, text='Route updated.')


def download_file(update, data):
    filename = update.message.document.file_name
    url = data.file_path
    file_path = os.path.join(download_path, filename)

    urlopener = URLopener()
    urlopener.retrieve(url, file_path)

    return file_path


def add_night(lines):
    lines.append('n ' + night_type)
    return lines


def save_to_file(lines):
    route_path = os.path.join(routes_path, 'route.txt')
    with open(route_path, 'a') as route:
        formatted_lines = [line.strip() for line in lines]
        route.write('\n' + '\n'.join(formatted_lines))


def check_if_file_is_valid(lines):
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
    current_dir = os.getcwd()
    os.chdir(routes_path)
    subprocess.call(['git', 'pull'])
    subprocess.call(['git', 'add', '.'])
    message = '[route update]'
    subprocess.call(['git', 'commit', '-m', message])
    #subprocess.call(['git', 'push'])
    os.chdir(current_dir)
