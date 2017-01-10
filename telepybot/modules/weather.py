"""*Returns weather forecast for a location.*

This module can search weather reports using Wunderground API.
Weather reports consist of a current weather in observation location,
a 3 day weather forecast and distance from observation location to
the requested location. Module also features an interactive mode where user
can search new locations relative to the original location.

Usage:
```
  /weather
  /weather Palo Alto, CA
```

Interactive mode:
```
  [distance] [cardinal direction]
  100 NW  -  weather in 100km to northwest from original location
```
"""
import json
from math import asin, atan2, cos, degrees, pi, radians, sin, sqrt

#from telegram import KeyboardButton, ParseMode, ReplyKeyboardMarkup
import telegram
from geopy.geocoders import Nominatim

try:
    # For Python 3.0 and later
    from urllib.request import urlopen
    from configparser import ConfigParser
except ImportError:
    # Fall back to Python 2's urllib
    from urllib import urlopen
    from ConfigParser import ConfigParser

config = ConfigParser()
config.read('telepybot.conf')
api_key = config.get('weather', 'wundergroundApiKey')


def handle_update(bot, update, update_queue, logger):
    """Get weather forecast for location from update.

    This is the main function that modulehander calls.

    Args:
        bot (telegram.Bot): Telegram bot itself
        update (telegram.Update): Update that will be processed
        update_queue (Queue): Queue containing all incoming and unhandled updates
        logger (Logger): Logger that writes to bots own log file.
    """
    chat_id = update.message.chat_id
    bot.sendChatAction(chat_id, action=telegram.ChatAction.TYPING)
    try:
        command = update.message.text.split(' ', 1)[1]
    except IndexError:
        command = ''
    finally:
        message = update.message

    location = None
    while not location:
        #text = ("Please send a location or type a city.\nYou may also "
        #        "cancel by typing \"cancel\"")
        text = "Please send a location or type a city."

        if message.location:
            reply_markup = telegram.ReplyKeyboardHide()
            bot.sendMessage(
                chat_id=chat_id,
                text="Searching forecast.",
                reply_markup=reply_markup)
            bot.sendChatAction(chat_id, action=telegram.ChatAction.TYPING)
            location = parse_location(message.location)
        elif command != '':
            if command.lower() == 'cancel':
                reply_markup = telegram.ReplyKeyboardHide()
                bot.sendMessage(
                    chat_id=chat_id,
                    text="Cancelled.",
                    reply_markup=reply_markup)
                return
            try:
                geolocator = Nominatim()
                geo_code = geolocator.geocode(command)
                if not geo_code:
                    raise ValueError("geolocator.geocode() returned None")
                reply_markup = telegram.ReplyKeyboardHide()
                bot.sendMessage(
                    chat_id=chat_id,
                    text="Searching forecast.",
                    reply_markup=reply_markup)
                location = parse_location(geo_code)
            except ValueError as e:
                logger.info("location %s caused error %s" % (command, e))
                text = "Couldn't find that location. Try anothet location"
                bot.sendMessage(chat_id=chat_id, text=text)
                message = update_queue.get().message
                if message.text.startswith('/'):
                    # User accesses antoher module
                    update_queue.put(update)
                    return
                command = message.text
                bot.sendChatAction(chat_id, action=telegram.ChatAction.TYPING)
                # TODO: fix this horrible structure
        else:
            location_keyboard = telegram.KeyboardButton(
                text='Send location', request_location=True)
            reply_markup = telegram.ReplyKeyboardMarkup(
                [[location_keyboard], ['Cancel']])
            bot.sendMessage(
                chat_id=chat_id, text=text, reply_markup=reply_markup)
            message = update_queue.get().message

            if message.text.startswith('/'):
                # User accesses antoher module
                update_queue.put(update)
                return
            command = message.text
            bot.sendChatAction(chat_id, action=telegram.ChatAction.TYPING)

    report = construct_report(location)
    bot.sendMessage(
        chat_id=chat_id, text=report, parse_mode=telegram.ParseMode.MARKDOWN)

    # Interactive mode, where user can change location e.g. "100 N"
    text = """To search weather for relative position,
              type [distance in km] [direction], e.g. "100 N"."""
    bot.sendMessage(chat_id=chat_id, text=text)

    while True:
        update = update_queue.get()
        bot.sendChatAction(chat_id, action=telegram.ChatAction.TYPING)
        try:
            distance, direction = update.message.text.split()
            distance = int(distance)
            new_location = calculate_new_query(location, distance, direction)
            bot.sendMessage(
                chat_id=chat_id,
                text=construct_report(new_location),
                parse_mode=telegram.ParseMode.MARKDOWN)
        except ValueError:
            if update.message.text.startswith('/'):
                # User accesses antoher module
                update_queue.put(update)
            else:
                text = "Invalid command. Interaction stopped"
                bot.sendMessage(chat_id=chat_id, text=text)
            break


def construct_report(query):
    """Construct the weather report that will be sent to user."""

    response = urlopen('http://api.wunderground.com/api/' + api_key +
                       '/conditions/forecast/alert/q/' + query + '.json')

    # Python 3 compatibility
    response_str = response.read().decode('utf-8')
    text = json.loads(response_str)

    try:
        error = text['response']['error']['type']
        if error == 'querynotfound':
            return "Sorry, couldn't fetch weather report from that location"
    except KeyError:
        pass

    curr = text['current_observation']

    distance = calculate_distance(
        float(query.split(',')[1]), float(query.split(',')[0]),
        float(curr['observation_location']['longitude']),
        float(curr['observation_location']['latitude']))

    bearing = calculate_direction(
        float(query.split(',')[0]), float(query.split(',')[1]),
        float(curr['observation_location']['latitude']),
        float(curr['observation_location']['longitude']))

    # Build report which contains location, current observation etc.
    report = ('*{}*\nAccuracy: {}km {}\n{}\n{}, {}C, {}km/h, '
              '{}mm past hour\n\n').format(
                  curr['observation_location']['full'], distance, bearing,
                  curr['observation_time'], curr['weather'], curr['temp_c'],
                  curr['wind_kph'], curr['precip_1hr_metric'])

    forecast = text['forecast']['txt_forecast']['forecastday']

    # Forecast for several time periods
    for i in range(1, 8):
        report += '*{}:* {} Probability for precipitation: {}%\n\n'.format(
            forecast[i]['title'], forecast[i]['fcttext_metric'],
            forecast[i]['pop'])

    return report


def calculate_distance(lon1, lat1, lon2, lat2):
    """Calculate the great circle distance between two
    coordinate points
    """

    # convert decimal degrees to radians
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    # haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
    c = 2 * asin(sqrt(a))
    r = 6371  # earth radius in km
    return "{0:.2f}".format(r * c)  # Leave two decimals and convert to string


def calculate_direction(lat1, lon1, lat2, lon2):
    """Calculate compass bearing from starting point to
    the end point and then convert it to a cardinal direction.
    """

    lat1rad = radians(lat1)
    lat2rad = radians(lat2)
    dlon = radians(lon2 - lon1)

    x = sin(dlon) * cos(lat2rad)
    y = cos(lat1rad) * sin(lat2rad) - sin(lat1rad) * cos(lat2rad) * cos(dlon)

    init_bearing = degrees(atan2(x, y))
    compass_bearing = init_bearing % 360

    directions = ["N", "NE", "E", "SE", "S", "SW", "W", "NW", "N"]
    i = int(round(compass_bearing / 45))
    return directions[i]


def calculate_new_query(old_query, distance, direction):
    """Find new location from interactive mode."""

    angle = {
        'N': 0,
        'NE': pi / 4,
        'E': pi / 2,
        'SE': 3 * pi / 4,
        'S': pi,
        'SW': 5 * pi / 4,
        'W': 3 * pi / 2,
        'NW': 7 * pi / 4
    }
    r = 6371  # earth radius in km
    dist = float(distance) / r  # angular distance

    old_lat, old_lon = old_query.split(',')
    old_lat = radians(float(old_lat))
    old_lon = radians(float(old_lon))

    new_lat = asin(
        sin(old_lat) * cos(dist) + cos(old_lat) * sin(dist) * cos(angle[
            direction.upper()]))

    new_lon = old_lon + atan2(
        sin((angle[direction.upper()])) * sin(dist) * cos(old_lat), cos(dist) -
        sin(old_lat) * sin(new_lat))

    return '{},{}'.format(degrees(new_lat), degrees(new_lon))


def parse_location(location):
    """Convert location to string, e.g. "60.161928,24.951688"
    """

    return str(location.latitude) + ',' + str(location.longitude)
