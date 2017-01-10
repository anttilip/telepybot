"""Builds elevation graph between one or more points.

Module searches route between two coordinate points, draws a
elevation graph and constructs a summary. Route and elevation are fetched
using Google Maps APIs. Graph is created from fetched elevation points and
drawn with Matplotlib.

Usage:
  Find elevation from Helsinki - Turku - Tampere
  /ele helsinki; turku; tampere

  /ele
  Helsinki
  via
  Turku
  tampere

You can replace any or all cities with location
"""
import json

import matplotlib
# yapf: disable
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from geopy.geocoders import GoogleV3, Nominatim
from PIL import Image

from telegram import ChatAction, Location, ParseMode

try:
    # For Python 3.0 and later
    from urllib.request import urlopen
    from urllib.parse import urlencode
    from configparser import ConfigParser
except ImportError:
    # Fall back to Python 2's urllib
    from urllib import urlopen
    from urllib import urlencode
    from ConfigParser import ConfigParser

# yapf: enable

config = ConfigParser()
config.read('telepybot.conf')
api_key = config.get('elevation', 'gmapsApiKey')


def handle_update(bot, update, update_queue, **kwargs):
    """Process message from update and send elevation infromation.

    This is the main function that modulehander calls.

    Args:
        bot (telegram.Bot): Telegram bot itself
        update (telegram.Update): Update that will be processed
        update_queue (Queue): Queue containing all incoming and unhandled updates
        kwargs: All unused keyword arguments. See more from python-telegram-bot
    """
    chat_id = update.message.chat_id
    origin = None
    destination = None
    via_locs = []

    try:
        query = update.message.text.split(' ', 1)[1]
        origin = query
        try:
            # TODO: Add possibility to add 'via' by chaining locations with ';'
            locs = query.split(';')
            origin = locs[0]
            if len(locs) > 1:
                destination = locs[-1].strip()
                via_locs = locs[1:-1]
                via_locs = [x.strip() for x in via_locs]
        except ValueError:
            pass
    except IndexError:
        pass

    next_is_via = False
    while not origin or not destination:
        text = ('Send location or place name')
        bot.sendMessage(chat_id=chat_id, text=text)
        update = update_queue.get()

        if update.message.location:
            location = update.message.location
        elif update.message.text != '':
            if update.message.text.startswith('/'):
                update_queue.put(update)
                return
            if update.message.text.lower().strip() == 'via':
                bot.sendMessage(chat_id=chat_id, text='Send via location')
                next_is_via = True
                continue
            geolocator = GoogleV3(api_key=api_key)
            location = geolocator.geocode(update.message.text)

        if next_is_via:
            next_is_via = False
            if not origin:
                text = "Via can't be before origin. Quitting"
                bot.sendMessage(chat_id=chat_id, text=text)
                return
            via_locs.append('{},{}'.format(location.latitude,
                                           location.longitude))
        elif origin:
            destination = '{},{}'.format(location.latitude, location.longitude)
        else:
            origin = '{},{}'.format(location.latitude, location.longitude)

    bot.sendChatAction(chat_id, action=ChatAction.TYPING)
    report, graph = elevate(origin, destination, via_locs, 'best')
    bot.sendMessage(chat_id, report, parse_mode=ParseMode.MARKDOWN)
    # bot.sendMessage(chat_id, 'If you want graph, type "graph"')
    with open(graph, 'rb') as photo:
        bot.sendChatAction(chat_id, action=ChatAction.UPLOAD_PHOTO)
        bot.sendPhoto(chat_id, photo)


def elevate(origin, destination, via_locs, plot_mode):
    """Get elevation data from Google Maps Elevation api and construct a report

    Receives origin, destination and possibly intermediate location points,
    finds a route using Google Maps Directions API. Gets altitude points for
    that route from Google Maps Elevation API. Calculates a few statistics and
    sends them to user along with a graph showing altitude along the route.

    Args:
        origin (str): Origin coordinates, e.g. "60.161928,24.951688"
        destination (str): Destination coordinates, e.g. "61.504956,23.743120"
        via_locs (list): Additional intermediate coordinates
        plot_mode (str): Preset mode for graph
    """

    params = {'origin': origin.encode('utf8'),
              'destination': destination.encode('utf8'),
              'waypoints': '|'.join('via:' + str(x) for x in via_locs),
              'key': api_key,
              'mode': 'bicycling',
              'avoid': 'highways'}

    cycling = True
    url_params = urlencode(params)
    url = 'https://maps.googleapis.com/maps/api/directions/json?' + url_params

    cycle_route = urlopen(url).read().decode('utf-8')
    route_json = json.loads(cycle_route)

    # Since some countries don't have cycling routes, fall back to walking
    if route_json['status'] != "OK":
        # Change cycling to walking
        params['mode'] = 'walking'
        cycling = False

        url_params = urlencode(params)
        url = 'https://maps.googleapis.com/maps/api/directions/json?' + url_params

        walking_route = urlopen(url).read().decode('utf-8')
        route_json = json.loads(walking_route)

        if route_json['status'] != "OK":
            return "Could not find a route between the locations", None

    encoded_polyline = route_json['routes'][0]['overview_polyline']['points']
    distance = route_json['routes'][0]['legs'][0]['distance']['value'] / float(
        1000)

    params = {'path': 'enc:' + encoded_polyline,
              'samples': 128,
              'key': api_key}

    url_params = urlencode(params)

    url = 'https://maps.googleapis.com/maps/api/elevation/json?' + url_params

    elevation_data = urlopen(url).read().decode('utf-8')
    elevation_json = json.loads(elevation_data)

    elevation_points = []
    closest_to_via_locs = []
    for point in elevation_json['results']:
        elevation_points.append(point['elevation'])

    filename = build_plot(distance, elevation_points, plot_mode)

    # Choose correct mode for Google Maps link
    if cycling:
        mode = '1'
    else:
        # walking
        mode = '2'

    # Construct Google Maps link
    gmaps = 'https://www.google.com/maps/dir/%s/%s/%s/data=!4m2!4m1!3e%s' % (
        origin, '/'.join(str(x) for x in via_locs), destination, mode)

    # Calculate total ascent and descent
    ascent, descent = calculate_route_stats(elevation_points)

    report = ("From %s to %s\nDistance: %s km\nTotal ascent: %sm\n"
              "Total descent: %sm\n[Gmaps route link](%s)" %
              (origin, destination, "%.2f" % round(distance, 2), str(ascent),
               str(descent), gmaps))

    return report, filename


def build_plot(distance, elevation_points, plot_mode):
    """Build the elevation graph using matplotlib."""

    if plot_mode == 'tall':
        custom_dpi = 75
        size = (600 / custom_dpi, 200 / custom_dpi)
        convert_to_jpg = True
    elif plot_mode == 'best':
        custom_dpi = None
        size = None
        convert_to_jpg = False
    else:
        custom_dpi = 75
        size = (600 / custom_dpi, 200 / custom_dpi)
        convert_to_jpg = True

    plt.style.use('seaborn-darkgrid')
    # plt.style.use('ggplot')

    fig = plt.figure(figsize=size, dpi=custom_dpi)
    ax = fig.add_subplot(111)

    plt.ylabel('Elevation (m)')
    plt.xlabel('Distance (km)')

    x = np.linspace(0, distance, len(elevation_points))
    y = elevation_points
    ax.plot(x, y)

    plt.tight_layout()

    fig.savefig('.tmp/latest_elevation.png', dpi=custom_dpi)
    # Close plt window, figure and axis
    plt.close()
    if convert_to_jpg:
        Image.open('.tmp/latest_elevation.png').save(
            '.tmp/latest_elevation.jpg', 'JPEG')
        return '.tmp/latest_elevation.jpg'
    else:
        return '.tmp/latest_elevation.png'


def calculate_route_stats(elevation_points):
    """Calculate few statistics from elevation points."""
    total_ascent = 0
    total_descent = 0
    curr = elevation_points[0]

    for point in elevation_points:
        if point > curr:
            total_ascent += point - curr
        else:
            total_descent += curr - point
        curr = point

    return int(total_ascent), int(total_descent)


def parse_location(loc, destination=None):
    """Convert location to string, e.g. "60.161928,24.951688".
    """
    if isinstance(loc, Location):
        return str(loc.latitude) + ',' + str(loc.longitude)
    elif destination:
        return str(loc) + ',' + str(destination)
