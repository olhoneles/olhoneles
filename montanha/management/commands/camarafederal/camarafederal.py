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
from datetime import datetime, date
from montanha.models import ArchivedExpense, CollectionRun
from collector import CamaraFederalCollector
from updater import CamaraFederalUpdater
from parser import CamaraFederalParser


max_collectors = cpu_count() * 2
max_updaters = 1


class CamaraFederal(object):
    def __init__(self, collection_runs, debug_enabled):
        self.debug_enabled = debug_enabled
        self.collection_runs = collection_runs
        self.collector = CamaraFederalCollector()
        self.parser = CamaraFederalParser()
        self.updater = CamaraFederalUpdater(debug_enabled)
        self.stdout_mutex = Lock()
        self.expenses_mutex = Lock()

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

    # FIXME: copied from BaseCollector, needs to be shared!
    def debug(self, message):
        if self.debug_enabled:
            print message

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
    # end copied block

    def _collect_expenses(self, legislator_queue, expenses_queue):
        myname = current_process().name
        with self.stdout_mutex:
            print '[%s] started' % (myname)

        items = 0
        while True:
            try:
                mandate = legislator_queue.get(block=False)
                legislator = mandate.legislator
            except Empty:
                # Empty is also raised if queue item is not available, so checking...
                if not legislator_queue.empty():
                    continue
                break
            else:
                for year in range(self.updater.legislature.date_start.year, self.updater.legislature.date_end.year + 1):
                    for month in range(1, 13):
                        content = self.collector.retrieve_total_expenses_per_nature(legislator, year, month)
                        natures = self.parser.parse_total_expenses_per_nature(content)
                        self.updater.update_expense_natures(natures)

                        for nature in natures:
                            with self.stdout_mutex:
                                print '[%s] Retrieving expenses with %s by %s on %d-%d' % (myname, nature['name'], unicode(legislator), year, month)
                            content = self.collector.retrieve_nature_expenses(mandate.legislator, nature['original_id'], year, month)
                            expenses = self.parser.parse_nature_expenses(content, nature, year, month)
                            items += len(expenses)
                            item = {'mandate': mandate, 'nature': nature, 'expenses': expenses}
                            expenses_queue.put(item)

        with self.expenses_mutex:
            self.total_expenses += items

        with self.stdout_mutex:
            print '[%s] finished. %s: %d expenses collected.' % (myname, unicode(legislator), total)

    def _update_expenses(self, expenses_queue, finished):
        myname = current_process().name

        with self.stdout_mutex:
            print '[%s] started' % (myname)

        items = 0

        informed = False
        while items < self.total_expenses:
            try:
                item = expenses_queue.get(block=False)
                informed = False
            except Empty:
                pass
            else:
                items += 1
                self.updater.update_nature_expenses(item['mandate'], item['nature'].original_id, item['expenses'])
                if not informed and (items % 100 == 0 or items > (total_expenses - 10)):
                    with self.stdout_mutex:
                        print('[%s] %d items processed.' % (myname, items))
                    informed = True

        finished.set()

    def collect_expenses(self, legislature_id=None):
        with self.expenses_mutex:
            self.total_expenses = 0

        if legislature_id is None:
            legislature = self.updater.last_legislature()
        else:
            legislature = self.updater.get_legislature(legislature_id)

        # set the collection run and the legislature in the updater
        self.updater.collection_run = self.create_collection_run(legislature)
        self.updater.legislature = legislature

        with self.stdout_mutex:
            print '[CamaraFederal] Retrieving expenses'

        # Parallel collect
        legislator_queue = Queue()
        expenses_queue = Queue()
        updater_finished = Event()

        mandates = self.updater.get_mandates()
        self._fill_queue_from_list(mandates, legislator_queue)

        process_list = self._start_collectors(self._collect_expenses, legislator_queue, expenses_queue)
        self._start_updaters(self._update_expenses, expenses_queue, updater_finished)
        self._wait(process_list, updater_finished)

        with self.stdout_mutex:
            print '[CamaraFederal] Finished retrieving expenses' % self.total_legislators
