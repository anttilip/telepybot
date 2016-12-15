# -*- coding: utf-8 -*-
from telegram.file import File
from response import Response
from urllib2 import urlopen
#from kakku_help import gmaps, git
from kakku_help import pb
import json
import os
import sys
import subprocess
from math import sin, cos, radians, asin, sqrt
import numpy as np
import matplotlib.pyplot as plt
try:
    # For Python 3.0 and later
    from urllib.request import urlencode, URLopener
except ImportError:
    # Fall back to Python 2's urllib2
    from urllib2 import urlencode, URLopener


night_type = 't'


def handle_update(bot, update, update_queue, **kwargs):
    chat_id = update.message.chat_id
    text = 'Send your gps file or change the night type, e.g. "h" or "t c".'
    bot.sendMessage(chat_id=chat_id, text=text)

    while True:
        update = update_queue.get()
        bot.sendChatAction(chat_id, action=ChatAction.TYPING)
        if update.message.document:
            handle_gps()
            break
        elif update.message.text.lower() == "cancel":
            return
        elif update.message.text.lower() == "done":
            update_night()
        elif update.message.text.lower() != "":
            global night_type
            night_type = night
            text = "Night type set to 'n {}'\nIf that is " \
                       "not correct, start again by typing " \
                       "'gps.'\nSend gps file or type 'done' " \
                       "to send just location.".format(night_type)
           bot.sendMessage(chat_id=chat_id, text="Send blog file")
        elif update.message.text.startswith('/'):
            # User accesses another bot
            update_queue.put(update)
            break
        else:
            bot.sendMessage(chat_id=chat_id, text="Night type must start with 't' or 'h'")

def handle_gps(bot, update):
    path, filename = download_file(request.data.file_path,
                                   request.command.file_name)

    lines = []
    with open(path, 'r') as gpsfile:
        # Splits lines to list and removes empty lines from the end
        lines = gpsfile.read().strip().split('\n')

    file_is_valid, error_message = check_if_file_is_valid(lines)
    if not file_is_valid:
        text = 'File not valid: ' + error_message
        pb.push_note('GPS-analyzer', text)
        bot.sendMessage(chat_id=chat_id, text=text)

    add_night(lines)
    save_to_file(lines)
    #git()
    #git.commit_push('/home/pi/RaspberryPi-Scripts/jaakkolipsanen.github.io', '[route update]')

    report, graph = build_report(lines, filename)
    if graph:
        report += '\nIf you want graph (~20kB), type "graph"'
    else:
        report += '\nGraph is not avaliable.'

    pb.push_note('GPS-analyzer', 'Push complete')
    bot.sendMessage(chat_id=chat_id, text=report)

    if request.command.lower().strip() == 'graph':
        response = Response()
        response.photo = graph
        yield request.exit(response)
    else:
    if isinstance(request.command, basestring) and request.command.lower().strip() == 'done':
        save_to_file(['n ' + night_type])
            git()
            yield request.exit('Night location added and pushed')
        yield request.exit('Not a valid gps file. Aborting.')


def process(request):
    if not request.data:
        yield request.set_response(
                'Send your gps file or change '
                ' the night type, e.g. "h" or "t c".')

    if isinstance(request.command, basestring):
        night = request.command.lower().strip()
        if night.startswith('t') or night.startswith('h'):
                global night_type
                night_type = night
                response = "Night type set to 'n {}'\nIf that is " \
                           "not correct, start again by typing " \
                           "'gps.'\nSend gps file or type 'done' " \
			   "to send just location.".format(night_type)

                yield request.set_response(response)
        else:

            yield request.exit("Night type must start with 't' or 'h'")

    if isinstance(request.data, File):
        path, filename = download_file(request.data.file_path,
                                       request.command.file_name)

        lines = []
        with open(path, 'r') as gpsfile:
            # Splits lines to list and removes empty lines from the end
            lines = gpsfile.read().strip().split('\n')

        file_is_valid, error_message = check_if_file_is_valid(lines)
        if not file_is_valid:
            pb.push_note('GPS-analyzer', 'File not valid')
            yield request.exit(error_message)

        add_night(lines)
        save_to_file(lines)
        git()
        #git.commit_push('/home/pi/RaspberryPi-Scripts/jaakkolipsanen.github.io', '[route update]')

        report, graph = build_report(lines, filename)
        if graph:
            report += '\nIf you want graph (~20kB), type "graph"'
        else:
            report += '\nGraph is not avaliable.'

        pb.push_note('GPS-analyzer', 'Push complete')
        yield request.set_response(report)

        if request.command.lower().strip() == 'graph':
            response = Response()
            response.photo = graph
            yield request.exit(response)
    else:
	if isinstance(request.command, basestring) and request.command.lower().strip() == 'done':
	    save_to_file(['n ' + night_type])
            git()
            yield request.exit('Night location added and pushed')
        yield request.exit('Not a valid gps file. Aborting.')

def download_file(url_path, filename):
    filename, ext = filename.rsplit('.', 1)
    gpsfile = URLopener()
    file_path = '.downloads/%s.%s' % (filename, ext)
    gpsfile.retrieve(url_path, file_path)
    return file_path, filename

def add_night(lines):
    lines.append('n ' + night_type)
    return lines

def save_to_file(lines):
    route_path = '/home/pi/RaspberryPi-Scripts/jaakkolipsanen.github.io/cycle/routes/israel&jordan2016/route.txt'
    with open(route_path, 'a') as route:
        route.write('\n' + '\n'.join(lines))

def git():
    os.chdir('/home/pi/RaspberryPi-Scripts/jaakkolipsanen.github.io')
    subprocess.call(['git', 'pull'])
    subprocess.call(['git', 'add', '.'])
    subprocess.call(['git', 'commit', '-m', '[route update]'])
    subprocess.call(['git', 'push'])
    os.chdir('/home/pi/Telegram-bot')

def build_report(lines, filename):
    points = []
    for line in lines:
        if line != '' and line[0] != 'n':
            lat, lon = line.split(' ')
            points.append((float(lat), float(lon)))

    distance = calclulate_route_distance(points)
    report = '\nTotal distance: ' + '{0:.2f}'.format(distance) + 'km'

    elevation_points = get_elevations(points)
    report += calculate_route_stats(elevation_points)

    if elevation_points:
        filename += '.png'
        filename = build_plot(distance, elevation_points, filename)
        return report, str(filename)
    else:
        return report, None


def calclulate_route_distance(points):
    tot_dist = 0
    prev_point = points[0]
    for point in points:
        tot_dist += calculate_2point_distance(prev_point, point)
        prev_point = point

    return tot_dist


def calculate_route_stats(elevation_points):
    total_ascent = 0
    total_descent = 0
    highest_ele = -500
    curr = elevation_points[0]

    for point in elevation_points:
        if point > curr:
            total_ascent += point - curr
        else:
            total_descent += curr - point
        if point > highest_ele:
            highest_ele = point
        curr = point

    total_ascent = int(round(total_ascent))
    total_descent = int(round(total_descent))

    return ('\nHighest elevation: {}m\nTotal ascent: {}m\n'
            'Total descent: {}m'.format(int(highest_ele),
               total_ascent, total_descent))


def calculate_2point_distance(point1, point2):
    """Calculate the great circle distance between two
    coordinate points
    """
    lat1, lon1 = point1
    lat2, lon2 = point2

    # convert decimal degrees to radians
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    # haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    r = 6371 # earth radius in km
    return r * c

def get_elevations(points):
    #path = 'enc:' + gmaps.encode_polyline(points)
    #elevation_points = gmaps.get_elevation_path(path)
    #return elevation_points

    api_key = get_api_key()
    locations = 'enc:' + encode_polyline(points)

    params = {'locations': locations,
              'key': api_key}

    url_params = urlencode(params)
    url = 'https://maps.googleapis.com/maps/api/elevation/json?' + \
          url_params

    try:
        elevation_data = urlopen(url).read()
    except:
        return None

    elevation_json = json.loads(elevation_data)
    elevation_points = []

    for point in elevation_json['results']:
        elevation_points.append(point['elevation'])

    return elevation_points


def get_api_key():
    with open('auth/gmapsAuth.txt', 'r') as auth:
        return auth.read()


def build_plot(distance, elevation_points, filename):
    plt.switch_backend('agg')
    plt.style.use('seaborn-darkgrid')
    # plt.style.use('ggplot')

    fig = plt.figure()
    ax = fig.add_subplot(111)

    plt.ylabel('Elevation (m)')
    plt.xlabel('Distance (km)')

    x = np.linspace(0, distance, len(elevation_points))
    y = elevation_points
    ax.plot(x, y)
    plt.tight_layout()

    filename = '.tmp/' + filename
    fig.savefig(filename)

    return filename


def encode_polyline(points):
    """Encodes a list of points into a polyline string.
    See the developer docs for a detailed description of this encoding:
    https://developers.google.com/maps/documentation/utilities/polylinealgorithm
    :param points: a list of lat/lng pairs
    :type points: list of dicts or tuples
    :rtype: string
    """
    last_lat = last_lng = 0
    result = ""

    for point in points:
        lat = int(round(point[0] * 1e5))
        lng = int(round(point[1] * 1e5))
        d_lat = lat - last_lat
        d_lng = lng - last_lng

        for v in [d_lat, d_lng]:
            v = ~(v << 1) if v < 0 else v << 1
            while v >= 0x20:
                result += (chr((0x20 | (v & 0x1f)) + 63))
                v >>= 5
            result += (chr(v + 63))

        last_lat = lat
        last_lng = lng

    return result


def check_if_file_is_valid(lines):
    for i in xrange(len(lines)):
        try:
            # Checks if line is a coordinate pair, raises ValueError if not
            lat, lon = lines[i].split()
            float(lat)
            float(lon)
        except ValueError:
            if lines[i] == '':
                # Invalid syntax if line is empty
                return False, "Invalid syntax.\nLine {} is empty.".format(i + 1)
            if lines[i] != 'n t' and lines[i] != 'n h':
                # Invalid syntax if line is not night location
                return False, "Invalid syntax in line {}\n'{}'".format(i + 1, lines[i][:-1])
            else:
                continue
        except:
            return False, "Unhandled exception {} on line '{}'".format(sys.exc_info()[:2], i+1)

    return True, None


# voi poistaa git(), get_elevations(), encode_polyline(), get_api_key()
