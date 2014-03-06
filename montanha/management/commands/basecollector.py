# -*- coding: utf-8 -*-
#
# Copyright (©) 2010-2013 Estêvão Samuel Procópio
# Copyright (©) 2010-2013 Gustavo Noronha Silva
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU Affero General Public License as
#  published by the Free Software Foundation, either version 3 of the
#  License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU Affero General Public License for more details.
#
#  You should have received a copy of the GNU Affero General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.

import time
import socket
import urllib
from datetime import datetime
from httplib import BadStatusLine, IncompleteRead
from urllib import urlretrieve
from urllib2 import urlopen, Request, URLError, HTTPError
from BeautifulSoup import BeautifulSoup, BeautifulStoneSoup
from montanha.models import *

__all__ = ['BaseCollector', 'BeautifulSoup', 'BeautifulStoneSoup', 'Request', 'urlopen', 'urlretrieve']

socket.setdefaulttimeout(20)
MAX_TRIES = 100000


class BaseCollector(object):
    def __init__(self, collection_runs, debug_enabled):
        self.debug_enabled = debug_enabled
        self.collection_runs = collection_runs

    def debug(self, message):
        if self.debug_enabled:
            print message

    def mandate_for_legislator(self, legislator, party):
        try:
            mandate = Mandate.objects.get(legislator=legislator, date_start=self.legislature.date_start)
        except Mandate.DoesNotExist:
            mandate = Mandate(legislator=legislator, date_start=self.legislature.date_start, party=party, legislature=self.legislature)
            mandate.save()
            self.debug("Mandate starting on %s did not exist, created." % self.legislature.date_start.strftime("%F"))
        return mandate

    def update_legislators(self):
        exception("Not implemented.")

    def create_collection_run(self, legislature):
        collection_run, created = CollectionRun.objects.get_or_create(date=date.today(),
                                                                      legislature=legislature)
        self.collection_runs.append(collection_run)

        # Keep only one run for a day. If one exists, we delete the existing collection data
        # before we start this one.
        if not created:
            self.debug("Collection run for %s already exists for legislature %s, clearing." % (date.today().strftime("%F"), legislature))
            ArchivedExpense.objects.filter(collection_run=collection_run).delete()

        return collection_run

    def update_data(self):
        self.collection_run = self.create_collection_run(self.legislature)
        for mandate in Mandate.objects.filter(date_start__year=self.legislature.date_start.year, legislature=self.legislature):
            for year in range(self.legislature.date_start.year, datetime.now().year + 1):
                self.update_data_for_year(mandate, year)

    def retrieve_uri(self, uri, data={}, headers={}, post_process=True):
        count = 0
        while True:
            try:
                if data:
                    req = Request(uri, urllib.urlencode(data), headers)
                else:
                    req = Request(uri, headers=headers)
                resp = urlopen(req)
                if post_process:
                    return self.post_process_uri(resp.read())
                return resp
            except (HTTPError, BadStatusLine, IncompleteRead, socket.timeout), e:
                if isinstance(e, HTTPError):
                    if e.getcode() == 404:
                        print "Unable to retrieve %s." % (uri)
                        return None
                    elif e.getcode() >= 499:
                        print "Unable to retrieve %s try(%d) - will try again in 10 seconds." % (uri, count)
                        count += 1
                    else:
                        raise HTTPError(e.url, e.code, e.msg, e.headers, e.fp)
                else:
                    print "Unable to retrieve %s try(%d) - will try again in 10 seconds." % (uri, count)
                    count += 1
            except URLError:
                print "Unable to retrieve %s try(%d) - will try again in 10 seconds." % (uri, count)
                count += 1

            if count > MAX_TRIES:
                raise RuntimeError("Error: Unable to retrieve %s; Tried %d times.\nLast exception: %s" % (uri, MAX_TRIES, e.message))

            time.sleep(10)

    def post_process_uri(self, contents):
        # Some sites are not in utf-8.
        try:
            contents = contents.decode('utf-8')
        except UnicodeDecodeError:
            try:
                contents = contents.decode('iso-8859-1')
            except Exception:
                pass
        return BeautifulSoup(contents, convertEntities=BeautifulStoneSoup.ALL_ENTITIES)
