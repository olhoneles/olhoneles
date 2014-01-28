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


from multiprocessing import Process, Queue, Lock, Event, current_process, cpu_count
from Queue import Empty
from datetime import datetime
from collector import CamaraFederalCollector
from updater import CamaraFederalUpdater
from parser import CamaraFederalParser


max_collectors = cpu_count() * 2
max_updaters = cpu_count()


class CamaraFederal(object):
    def __init__(self, debug_enabled, full_scan):
        self.full_scan = full_scan
        self.collector = CamaraFederalCollector()
        self.parser = CamaraFederalParser()
        self.updater = CamaraFederalUpdater(debug_enabled)
        self.stdout_mutex = Lock()

    # Paralell Collector helpers
    @staticmethod
    def _fill_queue_from_list(items, queue):
        for i in items:
            queue.put(i)

    @staticmethod
    def _start_collectors(function, input_queue, output_queue=None):
        process_list = []

        for i in range(max_collectors):
            p = Process(name='%s %d' % ('Collector', i), target=function, args=(input_queue, output_queue,))
            process_list.append(p)
            p.start()

        return process_list

    @staticmethod
    def _start_updaters(function, input_queue, finished_event):
        process_list = []

        for i in range(max_updaters):
            p = Process(name='%s %d' % ('Updater', i), target=function, args=(input_queue, finished_event))
            p.daemon = True
            process_list.append(p)
            p.start()

        return process_list

    @staticmethod
    def _wait(collectors, finished_event):
        for p in collectors:
            p.join()

        finished_event.wait()

    # Paralel Collector implementation
    def _collect_pictures(self, picture_uri_queue, picture_queue):
        myname = current_process().name
        with self.stdout_mutex:
            print '[%s] started' % (myname)

        items = 0
        while True:
            try:
                legislator = picture_uri_queue.get(block=False)
                uri = legislator['picture_uri']
            except Empty:
                # Empty is also raised if queue item is not available, so checking...
                if not picture_uri_queue.empty():
                    continue
                break
            else:
                items += 1
                legislator['picture'] = self.collector.retrieve_legislator_picture(legislator)
                picture_queue.put(legislator)

        with self.stdout_mutex:
            print '[%s] finished. %d items processed.' % (myname, items)

    def _update_legislators(self, picture_queue, finished):
        myname = current_process().name
        informed_empty = False
        total_legislators = self.total_legislators

        with self.stdout_mutex:
            print '[%s] started' % (myname)

        items = 0

        informed = False
        while items < total_legislators:
            try:
                legislator = picture_queue.get(block=False)
                informed = False
            except Empty:
                pass
            else:
                items += 1
                self.updater.update_legislator(legislator)
                if not informed and (items % 100 == 0 or items > (total_legislators - 10)):
                    with self.stdout_mutex:
                        print('[%s] %d items processed.' % (myname, items))
                    informed = True

        finished.set()

    # Collector api used by Collect command
    def collect_legislatures(self):
        print '[CamaraFederal] Retrieving legislatures'

        content = self.collector.retrieve_legislatures()
        legislatures = self.parser.parse_legislatures(content)
        self.updater.update_legislatures(legislatures)

        print '[CamaraFederal] Retrieved %d legislatures' % len(legislatures)

    def collect_legislators(self, legislature_id=None):
        # Sequential collect
        if legislature_id is None:
            legislature = self.updater.last_legislature()
        else:
            legislature = self.updater.get_legislature(legislature_id)

        # set the legislature in the updater
        self.updater.legislature = legislature

        with self.stdout_mutex:
            print '[CamaraFederal] Retrieving legislators'

        content = self.collector.retrieve_legislators(legislature)
        legislators = self.parser.parse_legislators(content)

        self.total_legislators = len(legislators)

        # Paralell collect
        picture_uri_queue = Queue()
        picture_queue = Queue()
        updater_finished = Event()

        self._fill_queue_from_list(legislators, picture_uri_queue)

        process_list = self._start_collectors(self._collect_pictures, picture_uri_queue, picture_queue)

        self._start_updaters(self._update_legislators, picture_queue, updater_finished)

        self._wait(process_list, updater_finished)

        print '[CamaraFederal] Collected %s legislators' % self.total_legislators

    def collect_expenses(self, legislature_id=None):
        if legislature_id is None:
            legislature = self.updater.last_legislature()
        else:
            legislature = self.updater.get_legislature(legislature_id)

        # set the legislature in the updater
        self.updater.legislature = legislature

        with self.stdout_mutex:
            print '[CamaraFederal] Retrieving expenses'

        year = datetime.now().year
        month = 1
        #month = datetime.now().month

        mandates = self.updater.get_mandates()

        for mandate in mandates:
            content = self.collector.retrieve_total_expenses_per_nature(mandate.legislator, year, month)
            natures = self.parser.parse_total_expenses_per_nature(content)
            self.updater.update_expense_natures(natures)

            for nature in natures:
                db_total = self.updater.get_nature_total(mandate, nature['original_id'], year, month)
                if db_total is None or nature['total'] - db_total > 0.01:
                    print '[CamaraFederal] Retrieving expenses with %s by %s on %d-%d' % (nature['name'], unicode(mandate.legislator), year, month)
                    content = self.collector.retrieve_nature_expenses(mandate.legislator, nature['original_id'], year, month)
                    expenses = self.parser.parse_nature_expenses(content, nature, year, month)
                    self.updater.update_nature_expenses(mandate, nature['original_id'], expenses)
                else:
                    print '[CamaraFederal] Expenses with %s by %s on %d-%d are up to date' % (nature['name'], unicode(mandate.legislator), year, month)
