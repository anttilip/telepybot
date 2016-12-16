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
except ImportError:
    # Fall back to Python 2's urllib2
    from urllib2 import urlopen
    from urllib import urlencode

# yapf: enable

# TODO: make graph wider or width scales with distance


def handle_update(bot, update, update_queue, **kwargs):
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
            geolocator = GoogleV3(
                api_key='AIzaSyDSNzqPIM-JzwXVG-MmOZLTZ9aHz4X0KLo')
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
    api_key = get_api_key()

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


def get_api_key():
    with open('auth/gmapsAuth.txt', 'r') as auth:
        return auth.read()


def parse_location(loc, destination=None):
    if isinstance(loc, Location):
        return str(loc.latitude) + ',' + str(loc.longitude)
    elif destination:
        return str(loc) + ',' + str(destination)
