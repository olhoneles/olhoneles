# -*- coding: utf-8 -*-
#
# Copyright (©) 2015, Marcelo Jorge Vieira
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

import re
import time
from datetime import datetime

import requests
from django.core.management.base import BaseCommand
from BeautifulSoup import BeautifulSoup, BeautifulStoneSoup

from montanha.models import Supplier


class Command(BaseCommand):
    args = "<source> [debug]"
    help = "Update supplier data"

    def post_process_uri(self, contents):
        return BeautifulSoup(
            contents,
            convertEntities=BeautifulStoneSoup.ALL_ENTITIES
        )

    def debug(self, message):
        message = message.encode('utf-8')

        if self.debug_enabled:
            print message

        if not hasattr(self, 'logfile'):
            self.logfile = open(self.__class__.__name__.lower() + '.log', 'a')

        timestamp = datetime.fromtimestamp(time.time()).strftime('%F:%H:%M:%S')
        self.logfile.write('%s %s\n' % (timestamp, message))

    def get_item(self, class_name):
        data = self.html \
            .find("p", {"class": class_name}) \
            .find("span", {"class": "text"})
        return data

    def handle(self, *args, **options):
        self.debug_enabled = False
        self.only_empty = False

        if "debug" in args:
            self.debug_enabled = True

        if "only-empty" in args:
            self.only_empty = True

        suppliers = Supplier.objects.all()
        for supplier in suppliers:
            if self.only_empty and supplier.address:
                continue

            time.sleep(10)

            try:
                url = 'http://www.cnpjbrasil.com/e/cnpj/t/%s' % (
                    supplier.identifier
                )
                response = requests.get(url)
            except Exception as e:
                self.debug(u'Error on get %s: %s' % (supplier, str(e)))
                continue

            if response.status_code != 200:
                self.debug(u'Error on get %s: Status code is %d' % (
                    supplier, response.status_code)
                )
                continue

            contents = self.post_process_uri(response.text)
            if not contents:
                self.debug(
                    u'Error on get %s: There are no contents' % supplier
                )
                continue

            self.html = contents.find(id='details')
            if not self.html:
                self.debug(u'Error on get %s: There are no details' % supplier)
                continue

            trade_name = self.get_item('fantasia')
            if trade_name:
                supplier.trade_name = trade_name.text

            date_opened = self.get_item('opened')
            format_date = datetime.strptime(date_opened.text, '%d/%m/%Y')
            if format_date:
                supplier.date_opened = format_date

            # FIXME
            address = self.get_item('address')
            for e in address.findAll('br'):
                e.replaceWith(' ')
            if address:
                supplier.address = re.sub('<[^<]+?>', '', str(address))

            juridical_nature = self.get_item('nj')
            if juridical_nature:
                supplier.juridical_nature = juridical_nature.text

            economic_activity = self.get_item('ae1')
            if economic_activity:
                supplier.main_economic_activity = economic_activity.text

            status = self.get_item('status')
            if status:
                supplier.status = True if status.text == 'Ativa' else False

            supplier.save()

            self.debug(u'Supplier %s updated!' % supplier)
