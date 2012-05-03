import os
import time
from datetime import datetime

from logging import exception

import urllib
from urllib2 import urlopen, Request, URLError, HTTPError
from BeautifulSoup import BeautifulSoup, BeautifulStoneSoup

from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy import and_


appdir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
def get_database_path(house):
    return 'sqlite:///' + os.path.join(appdir, house, 'data.db')

def parse_money(string):
    string = string.strip('R$ ')
    string = string.replace('.', '')
    string = string.replace(',', '.')
    return float(string)

def parse_date(string):
    return datetime.strptime(string, '%d/%m/%Y').date()

class BaseCollector(object):
    debug = True

    def update_legislators(self):
        exception('Not implemented.')

    def update_data(self, year = datetime.now().year):
        exception('Not implemented.')

    def retrieve_uri(self, uri, data = {}, headers = {}):
        resp = None

        while True:
            try:
                req = Request(uri, urllib.urlencode(data), headers)
                resp = urlopen(req)
                break
            except HTTPError, e:
                if e.getcode() != 404:
                    raise HTTPError(e.url, e.code, e.msg, e.headers, e.fp)
            except URLError:
                print 'Unable to retrieve %s; will try again in 10 seconds.' % (uri)

            time.sleep(10)

        if not resp:
            return None

        contents = resp.read().decode('utf-8')

        return BeautifulSoup(contents)

    def get_element_from_uri(self, uri, element, attrs = {}, data = None):
        content = self.retrieve_uri (uri, data)
        return content.find(element, attrs)
