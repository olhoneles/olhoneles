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

import base64
import csv
import re
from datetime import datetime, date
from django.db import reset_queries
from basecollector import BaseCollector
from montanha.models import *


def parse_money(string):
    string = string.strip('R$ ')
    string = string.replace('.', '')
    string = string.replace(',', '.')
    string = string.replace('\r', '')
    return float(string)


def parse_date(string):
    return datetime.strptime(string, '%d/%m/%y').date()


class Senado(BaseCollector):
    def __init__(self, collection_runs, debug_enabled=False, full_scan=False):
        super(Senado, self).__init__(collection_runs, debug_enabled, full_scan)

        self.csv_regex = re.compile('http://www.senado.leg.br/transparencia/LAI/verba/2[0-9]{3}_SEN_[^\.]+.csv')

        institution, _ = Institution.objects.get_or_create(siglum='Senado', name=u'Senado Federal')
        self.legislature, _ = Legislature.objects.get_or_create(institution=institution,
                                                                date_start=datetime(2011, 1, 1),
                                                                date_end=datetime(2014, 12, 31))

    def retrieve_legislators(self):
        uri = 'http://www.senado.gov.br/transparencia/'
        return BaseCollector.retrieve_uri(self, uri)

    def retrieve_data_for_year(self, legislator, year):
        uri = 'http://www.senado.gov.br/transparencia/sen/verba/VerbaMes.asp'
        data = {
            'COD_ORGAO': legislator.original_id,
            'ANO_EXERCICIO': year,
        }
        headers = {
            'Referer': 'http://www.senado.gov.br/transparencia/sen/verba/verbaAno.asp',
            'Origin': 'http://www.senado.gov.br',
        }
        return BaseCollector.retrieve_uri(self, uri, data, headers)

    def update_legislators(self):
        page = self.retrieve_legislators()

        # We ignore the first one because it is a placeholder.
        options = page(attrs={'name': 'COD_ORGAO'})[0].findAll('option')[1:]

        # Turn the soup objects into a list of dictionaries
        legislators = []
        for item in options:
            name = ' '.join([x.title() for x in item.getText().split()])
            original_id = int(item.get('value'))
            legislators.append(dict(name=name, original_id=original_id))

        # Obtain the existing ids
        existing_ids = [x.id for x in Legislator.objects.filter(mandate__legislature=self.legislature).all()]

        # Add legislators that do not exist yet
        for l in legislators:
            if l['original_id'] in existing_ids:
                continue

            try:
                legislator = Legislator.objects.get(original_id=l['original_id'])
                self.debug("Found existing legislator: %s" % unicode(legislator))

                mandate = self.mandate_for_legislator(legislator, None)
            except Legislator.DoesNotExist:
                legislator = Legislator(name=l['name'], original_id=l['original_id'])
                legislator.save()

                mandate = Mandate(legislator=legislator, date_start=self.legislature.date_start, party=None, legislature=self.legislature)
                mandate.save()

                self.debug("New legislator found: %s" % unicode(legislator))

    def update_data_for_year(self, mandate, year=datetime.now().year):
        self.debug("Updating data for year %d" % year)

        data = self.retrieve_data_for_year(mandate.legislator, year)

        csv_data = None
        anchor = data.find('a', href=self.csv_regex)
        if anchor and anchor.get('href'):
            csv_data = unicode(self.retrieve_uri(anchor.get('href')))

        if not csv_data:
            self.debug("Legislator %s does not have expenses for year %d" % (mandate.legislator.name, year))
            return

        csv_data = [l.encode('utf-8') for l in csv_data.split('\n')]

        expected_headers = ["ANO", "MES", "SENADOR", "TIPO_DESPESA", "CNPJ_CPF",
                            "FORNECEDOR", "DOCUMENTO", "DATA", "DETALHAMENTO",
                            "VALOR_REEMBOLSADO"]
        headers = csv_data[1].split(';')
        if not len(headers) == len(expected_headers):
            print u'Bad CSV: expected %d headers, got %d' % (len(expected_headers), len(headers))
            return

        for i, header in enumerate(expected_headers):
            actual_header = headers[i].strip('"\r')
            if actual_header != header:
                print u'Bad CSV: expected header %s, got %s' % (header, actual_header)
                return

        for row in csv.reader(csv_data[2:], delimiter=";"):
            # Last row?
            if not row:
                continue

            nature = row[3].strip('"')
            cnpj = row[4].replace('.', '').replace('-', '').replace('/', '').strip('"')
            supplier_name = row[5].strip('"')
            docnumber = row[6].strip('"')

            try:
                expense_date = parse_date(row[7].strip('"'))
            except:
                expense_date = date(year, 1, 1)

            expensed = parse_money(row[9].strip('"\r'))

            try:
                nature = nature.decode('utf-8')
            except Exception:
                pass

            nature, _ = ExpenseNature.objects.get_or_create(name=nature)

            try:
                supplier_name = supplier_name.decode('utf-8')
            except Exception:
                pass

            try:
                docnumber = docnumber.decode('utf-8')
            except Exception:
                pass

            try:
                supplier = Supplier.objects.get(identifier=cnpj)
            except Supplier.DoesNotExist:
                supplier = Supplier(identifier=cnpj, name=supplier_name)
                supplier.save()

            expense = ArchivedExpense(number=docnumber,
                                      nature=nature,
                                      date=expense_date,
                                      expensed=expensed,
                                      mandate=mandate,
                                      supplier=supplier)
            self.debug("New expense found: %s" % unicode(expense))

            # This makes django release its queries cache; when running Django itself,
            # the queries are cleared for each request, not the case here, so we need
            # to do it ourselves.
            reset_queries()

    def _normalize_name(self, name):
        names_map = {
            'Gim': 'Gim Argello',
        }
        return names_map.get(name, name)

    def _normalize_party_name(self, name):
        names_map = {
            'PCdoB': 'PC do B',
        }
        return names_map.get(name, name)

    def update_legislators_extra_data(self):
        data = self.retrieve_uri('http://www.senado.gov.br/senadores/')
        table = data.find(id='senadores')
        for row in table.findAll('tr'):
            columns = row.findAll('td')
            if not columns:
                continue

            name = self._normalize_name(columns[0].getText())

            legislator = Legislator.objects.filter(name=name)
            legislator = legislator.filter(mandate__legislature=self.legislature)
            legislator = legislator.order_by("-mandate__date_start")[0]

            mandate = legislator.mandate_set.order_by("-date_start")[0]
            if mandate.legislature != self.legislature:
                print 'Legislature found for %s is not the same as the one we need, ignoring.' % legislator.name
                continue

            party = self._normalize_party_name(columns[1].getText())
            mandate.party, _ = PoliticalParty.objects.get_or_create(siglum=party)
            mandate.save()

            href = columns[6].findChild().get('href')
            if href:
                legislator.email = href.split(':')[1]

            href = columns[7].findChild().get('href')
            if href:
                legislator.site = href.split(':')[1]

            legislator.save()

            self.debug('Updated data for %s: %s, %s, %s' % (legislator.name,
                                                            mandate.party.name,
                                                            legislator.email,
                                                            legislator.site))
