# -*- coding: utf-8 -*-
#
# Copyright (©) 2010-2013 Estêvão Samuel Procópio
# Copyright (©) 2010-2013 Gustavo Noronha Silva
# Copyright (©) 2014 Lúcio Flávio Corrêa
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

from datetime import datetime, date
import time
import requests
from BeautifulSoup import BeautifulSoup, BeautifulStoneSoup
from montanha.models import Mandate, CollectionRun, ArchivedExpense


class BaseCollector(object):
    def __init__(self, collection_runs, debug_enabled):
        self.debug_enabled = debug_enabled
        self.collection_runs = collection_runs
        self.collection_run = None

        self.default_timeout = 20
        self.max_tries = 10
        self.try_again_timer = 10

    def debug(self, message):
        message = message.encode('utf-8')

        if self.debug_enabled:
            print message

        if not hasattr(self, 'logfile'):
            self.logfile = open(self.__class__.__name__.lower() + '.log', 'a')

        timestamp = datetime.fromtimestamp(time.time()).strftime('%F:%H:%M:%S')
        self.logfile.write('%s %s\n' % (timestamp, message))

    def mandate_for_legislator(self, legislator, party, state=None, original_id=None):
        try:
            mandate = Mandate.objects.get(legislator=legislator, date_start=self.legislature.date_start)
        except Mandate.DoesNotExist:
            mandate = Mandate(legislator=legislator, date_start=self.legislature.date_start, party=party,
                              legislature=self.legislature)
            mandate.save()
            self.debug("Mandate starting on %s did not exist, created." % self.legislature.date_start.strftime("%F"))

        if original_id:
            mandate.original_id = original_id
            mandate.save()

        return mandate

    def update_legislators(self):
        raise Exception("Not implemented.")

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
        for mandate in Mandate.objects.filter(date_start__year=self.legislature.date_start.year,
                                              legislature=self.legislature):
            for year in range(self.legislature.date_start.year, datetime.now().year + 1):
                self.update_data_for_year(mandate, year)

    def retrieve_uri(self, uri, data=None, headers=None, post_process=True, force_encoding=None, return_content=False):
        retries = 0

        pargs = (uri, unicode(data), unicode(headers), int(post_process), unicode(force_encoding))
        self.debug(u"Retrieving %s data: %s headers: %s post_process? %d force_encoding: %s" % pargs)

        while retries < self.max_tries:
            try:
                options = dict(data=data, headers=headers, timeout=self.default_timeout, stream=True)
                if data:
                    r = requests.post(uri, **options)
                else:
                    r = requests.get(uri, **options)

                if force_encoding:
                    r.encoding = force_encoding
                if r.status_code == requests.codes.not_found:
                    return False
                if post_process:
                    return self.post_process_uri(r.text)
                elif return_content:
                    return r.content
                else:
                    return r.text

            except requests.ConnectionError:
                retries += 1
                print "Unable to retrieve %s try(%d) - will try again in %d seconds." % (uri, retries, self.try_again_timer)

            time.sleep(self.try_again_timer)

        raise RuntimeError("Error: Unable to retrieve %s; Tried %d times." % (uri, self.max_tries))

    def _normalize_party_name(self, name):
        names_map = {
            'PCdoB': 'PC do B',
        }
        return names_map.get(name, name)

    def post_process_uri(self, contents):
        return BeautifulSoup(contents, convertEntities=BeautifulStoneSoup.ALL_ENTITIES)

    def normalize_cnpj_or_cpf(self, cnpj):
        return cnpj.replace('.', '').replace('-', '').replace('/', '').strip()
