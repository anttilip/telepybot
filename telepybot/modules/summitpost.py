#!/usr/bin/env python
# -*- coding: utf-8 -*-
from urllib2 import urlopen
import sys
from pprint import pprint
from bs4 import BeautifulSoup, NavigableString, Comment
from response import Response


def process(request):
    if not isinstance(request.command, basestring):
        request.exit('Use syntax "summitpost [location]". '
                     'For example: summipost halti')

    query = '+'.join(request.command.split())
    search_url = "http://www.summitpost.org/object_list.php?object_type=1&object_name_0=&object_name_1="
    print 'search: ' + search_url + query

    try:
        search_page = urlopen(search_url + query).read()
        soup = BeautifulSoup(search_page, "lxml")
        href = soup.find('td', class_='srch_results_lft').next['href']

        atricle_page = urlopen("http://www.summitpost.org" + href).read()
    except:
        yield request.exit('Could not find an article')

    # Load article page
    soup = BeautifulSoup(atricle_page, "lxml")
    # Get title, elevation, location etc. from article
    stats = get_stats(soup)

    # Build table of contents that is used in navigation
    table_of_contents = get_table_of_contents(soup)

    # report is sent to user
    report = "[Summitpost link](http://www.summitpost.org" + href + ')\n'
    report += stats

    # Append table of contents so user knows
    # which chapters and corresponding numbers
    report += '\n*Table of contents*\n'
    for key in table_of_contents.keys():
        report += str(key) + ': ' + table_of_contents[key] + '\n'

    article_by_chapters = get_navigation_dict(soup, table_of_contents)

    response = Response()
    # Report contains markdown syntax
    response.set_parse_markdown()
    response.set(report)

    yield request.set_response(response)

    # Interactive mode started after the first message
    # User can get specific chapters by typing the chapter number or "next"

    i = 1
    while request.command.lower().strip() != 'cancel':
        try:
            if request.command.lower().strip() == 'next':
                i += 1
                yield request.set_response(response.set(article_by_chapters[i]))
            elif request.command.lower().strip() == 'toc':
                toc = '*Table of contents*\n'
                for key in table_of_contents.keys():
                    toc += str(key) + ': ' + table_of_contents[key] + '\n'
                yield request.set_response(response.set(toc))
            elif request.command.lower().strip() == 'routes':
                while True:
                    message = handle_routes(soup, request)
                    if not message:
                        yield request.exit('Interaction ended.')
                    yield message
            else:
                i = int(request.command)
                article = article_by_chapters[i]
                response.set(article)
                yield request.set_response(response)
        except (ValueError, KeyError):
            raise
            yield request.set_response('Not a valid chapter')

    yield request.exit('Interaction ended.')


def get_stats(soup):
    data_box = soup.find('table', class_='data_box')

    report = ''
    stats = data_box.find_all('td')[2].find_all('p')
    for stat in stats:
        report += ' '.join(stat.get_text().split()) + '\n'

    return report


def get_table_of_contents(soup):
    table_of_contents = {}
    i = 1
    chapters = soup.find_all('h2')
    for chapter in chapters:
        table_of_contents[i] = chapter.get_text()
        i += 1
    return table_of_contents


def get_navigation_dict(soup, table_of_contents):
    article = soup.find('article')
    chapters = {}
    i = 1
    chapter = ''
    cur = article.find('h2', id='first_h2')
    while cur.next:
        if cur.name == 'p':
            chapter += cur.get_text() + '\n'
        elif cur.name == 'h2':
            if chapter != '':
                if len(chapter) > 4095:
                    chapter = chapter[:4045]
                    chapter += '... \n*Chapter too long. Read rest from the link.*'
                chapters[i] = chapter
                i += 1
            chapter = '*' + cur.get_text() + '*\n'
        elif isinstance(cur, NavigableString) and not isinstance(cur, Comment):
            if not cur.isspace():
                chapter += cur + '\n'
        cur = cur.next

    return chapters

def handle_routes(soup, request):
    print "handle_routes"
    try:
        routes = get_routes(soup)
    except:
        yield request.exit('Could not find routes. Aborting interaction')

    report = 'Choose one of these routes:\n'
    for key in routes.keys():
        report += str(key) + ': ' + routes[key][0]

    yield request.set_response(response.set(report))

    try:
        number = int(request.command)
        url = urlopen(routes[number][1]).read()
        soup = BeautifulSoup(url)
        table_of_contents = get_table_of_contents(soup)
        article_by_chapters = get_navigation_dict(soup, table_of_contents)
        report = 'Table of contents\n'
        for key in table_of_contents.keys():
            report += str(key) + ': ' + table_of_contents[key] + '\n'
        yield request.set_response(report)
    except:
        yield request.exit('Could not get a route. Aborting')

    print "ennen looppia"
    i = 1
    while request.command.lower().strip() != 'cancel':
        try:
            if request.command.lower().strip() == 'next':
                print "next"
                i += 1
                yield request.set_response(response.set(article_by_chapters[i]))
            else:
                print "numero"
                number = int(request.command)
                i += 1
                yield request.set_response(article_by_chapters[i])
        except:
            print "exception"
            yield request.exit('Could not get a route. Aborting')


def get_routes(soup):
    raw_routes = []
    curr = soup.find_all('div', class_='left_box_heading')[1]

    while curr.next_element:
        if curr.name == 'a' and curr.get_text() == 'Trip Reports':
            break
        if curr.name == 'a' and curr.get_text() != 'Routes':
            raw_routes.append((curr.get_text(), curr['href']))
        curr = curr.next_element

    routes = {}
    i = 1
    for route in raw_routes:
        baseurl = 'http://www.summitpost.org/'
        url = urlopen(baseurl + route[1]).read()
        route_soup = BeautifulSoup(url, "lxml")
        stats = "[Route link](" + baseurl + route[1] + ")\n"
        stats += get_stats(route_soup)
        routes[i] = (stats, baseurl + route[1])
        i += 1

    return routes


if __name__ == '__main__':
    query = '+'.join(sys.argv[1:])
    process(query)
