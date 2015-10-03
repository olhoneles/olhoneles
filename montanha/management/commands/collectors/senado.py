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

import re
from datetime import datetime
from StringIO import StringIO
from django.db import reset_queries
import pandas as pd
from basecollector import BaseCollector
from montanha.models import (ArchivedExpense, Institution, Legislature,
                             Legislator, Mandate, ExpenseNature, Supplier, PoliticalParty)

OBJECT_LIST_MAXIMUM_COUNTER = 1000


class Senado(BaseCollector):
    def __init__(self, collection_runs, debug_enabled=False):
        super(Senado, self).__init__(collection_runs, debug_enabled)

        institution, _ = Institution.objects.get_or_create(siglum='Senado', name=u'Senado Federal')
        self.legislature, _ = Legislature.objects.get_or_create(institution=institution,
                                                                date_start=datetime(2015, 1, 1),
                                                                date_end=datetime(2018, 12, 31))

    def retrieve_legislators(self):
        uri = 'http://www25.senado.leg.br/web/transparencia/sen/'
        return BaseCollector.retrieve_uri(self, uri, force_encoding='utf-8')

    def retrieve_data_for_year(self, year):
        uri = 'http://www.senado.gov.br/transparencia/LAI/verba/%d.csv' % year

        self.debug("Downloading %s" % uri)

        return BaseCollector.retrieve_uri(self, uri, force_encoding='windows-1252', post_process=False)

    def try_name_disambiguation(self, name):
        if name.title() == 'Luiz Henrique':
            return Legislator.objects.get(id=246), False

        return None, False

    def update_legislators(self):
        page = self.retrieve_legislators()

        # We ignore the first one because it is a placeholder.
        options = page(attrs={'name': 'frmConsulta1'})[0].findAll('option')[1:]

        # Turn the soup objects into a list of dictionaries
        legislators = []
        for item in options:
            name = ' '.join([x.title() for x in item.getText().split()])
            original_id = int(item.get('value'))
            legislators.append(dict(name=name, original_id=original_id))

        # Add legislators that do not exist yet
        for l in legislators:
            mandate = Mandate.objects.filter(legislature=self.legislature).filter(original_id=l['original_id'])
            if mandate.count():
                assert(mandate.count() == 1)
                mandate = mandate[0]
                legislator = mandate.legislator
                self.debug("Found existing legislator: %s" % unicode(legislator))
            else:
                legislator, created = self.try_name_disambiguation(l['name'])
                if not legislator:
                    legislator, created = Legislator.objects.get_or_create(name=l['name'])

                if created:
                    self.debug("New legislator: %s" % unicode(legislator))
                else:
                    self.debug("Found existing legislator: %s" % unicode(legislator))

                mandate = self.mandate_for_legislator(legislator, party=None, original_id=l['original_id'])

    def update_data(self):
        self.collection_run = self.create_collection_run(self.legislature)
        for year in range(self.legislature.date_start.year, datetime.now().year + 1):
            self.update_data_for_year(year)

    def update_data_for_year(self, year=datetime.now().year):
        self.debug("Updating data for year %d" % year)

        csv_data = self.retrieve_data_for_year(year)
        csv_data = re.sub(r'([^;])"([^;\n])', r'\1\"\2', csv_data)
        data = StringIO(csv_data)

        if data:
            df = pd.read_csv(data, skiprows=1, delimiter=";",
                             parse_dates=[7], decimal=',',
                             error_bad_lines=False,
                             encoding='utf-8').dropna(how='all')

            expected_header = [u'ANO',
                               u'MES',
                               u'SENADOR',
                               u'TIPO_DESPESA',
                               u'CNPJ_CPF',
                               u'FORNECEDOR',
                               u'DOCUMENTO',
                               u'DATA',
                               u'DETALHAMENTO',
                               u'VALOR_REEMBOLSADO']

            actual_header = df.columns.values.tolist()

            if actual_header != expected_header:
                print u'Bad CSV: expected header %s, got %s' % (expected_header, actual_header)
                return

            archived_expense_list = []
            objects_counter = 0
            archived_expense_list_counter = len(df.index)

            for idx, row in df.iterrows():
                name = row["SENADOR"]
                nature = row["TIPO_DESPESA"]
                cpf_cnpj = self.normalize_cnpj_or_cpf(row["CNPJ_CPF"])
                supplier_name = row["FORNECEDOR"]
                docnumber = row["DOCUMENTO"]
                expense_date = row["DATA"]
                expensed = row['VALOR_REEMBOLSADO']

                # FIXME: WTF?
                if isinstance(expensed, unicode):
                    expensed = float(expensed.replace(',', '.').replace('\r\n', ''))

                nature, _ = ExpenseNature.objects.get_or_create(name=nature)

                try:
                    supplier = Supplier.objects.get(identifier=cpf_cnpj)
                except Supplier.DoesNotExist:
                    supplier = Supplier(identifier=cpf_cnpj, name=supplier_name)
                    supplier.save()

                legislator, _ = self.try_name_disambiguation(name)
                if not legislator:
                    legislator = Legislator.objects.get(name__iexact=name)
                mandate = self.mandate_for_legislator(legislator, None)
                expense = ArchivedExpense(number=docnumber,
                                          nature=nature,
                                          date=expense_date,
                                          expensed=expensed,
                                          mandate=mandate,
                                          supplier=supplier,
                                          collection_run=self.collection_run)
                archived_expense_list.append(expense)
                self.debug("New expense found: %s" % unicode(expense))

                objects_counter += 1
                archived_expense_list_counter -= 1

                # We create a list with up to OBJECT_LIST_MAXIMUM_COUNTER.
                # If that lists is equal to the maximum object count allowed
                # or if there are no more objects in archived_expense_list,
                # we bulk_create() them and clear the list.

                if objects_counter == OBJECT_LIST_MAXIMUM_COUNTER or archived_expense_list_counter == 0:
                    ArchivedExpense.objects.bulk_create(archived_expense_list)
                    archived_expense_list[:] = []
                    objects_counter = 0
                    reset_queries()
        else:
            self.debug("Error downloading file for year %d" % year)

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
        # Disabled for now, page got redesigned
        return
        data = self.retrieve_uri('http://www.senado.gov.br/senadores/')
        table = data.find(id='senadores')
        for row in table.findAll('tr'):
            columns = row.findAll('td')
            if not columns:
                continue

            name = self._normalize_name(columns[0].getText())

            legislator = Legislator.objects.filter(name=name).filter(
                mandate__legislature=self.legislature
            ).order_by("-mandate__date_start")

            # Check if query returned a legislator
            if legislator.exists():
                # Get the first row of the query result
                legislator = legislator[0]

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
            else:
                self.debug('Legislator found on site but not on database: %s' % name)
