# -*- coding: utf-8 -*-
#
# Copyright (©) 2010-2013 Estêvão Samuel Procópio
# Copyright (©) 2010-2013 Gustavo Noronha Silva
# Copyright (©) 2014 Lúcio Flávio Corrêa
# Copyright (©) 2017, Marcelo Jorge Vieira
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

from datetime import datetime
from io import BytesIO

import rows
from django.db import reset_queries

from basecollector import BaseCollector
from montanha.models import (
    ArchivedExpense, Institution, Legislature,
    Legislator, Mandate, ExpenseNature, PoliticalParty
)


OBJECT_LIST_MAXIMUM_COUNTER = 1000


extract_text = rows.plugins.html.extract_text
extract_links = rows.plugins.html.extract_links


class Collector(BaseCollector):
    def __init__(self, collection_runs, debug_enabled=False):
        super(Collector, self).__init__(collection_runs, debug_enabled)

        self.institution, _ = Institution.objects.get_or_create(
            siglum='Senado', name=u'Senado Federal'
        )
        self.legislature = None
        transparencia_url = 'http://www25.senado.leg.br/web/transparencia/sen'
        self.legislature_data = [
            {
                'start': 2007,
                'end': 2010,
                'legislators': '{0}/outras-legislaturas/-/a/53/por-nome'.format(transparencia_url),
            },
            {
                'start': 2011,
                'end': 2014,
                'legislators': '{0}/outras-legislaturas/-/a/54/por-nome'.format(transparencia_url),
            },
            {
                'start': 2015,
                'end': 2018,
                'legislators': '{0}/em-exercicio/-/e/por-nome'.format(transparencia_url),
                'away_legislators': '{0}/fora-do-exercicio/-/f/por-nome'.format(transparencia_url),
            },
        ]

    def run(self):
        self.update_data()

    def get_legislature(self, data):
        legislature, created = Legislature.objects.get_or_create(
            institution=self.institution,
            date_start=datetime(data.get('start'), 1, 1),
            date_end=datetime(data.get('end'), 12, 31))

        if created:
            self.debug(u'New Legislature found: {0}'.format(legislature))
        else:
            self.debug(u'Found existing legislature: {0}'.format(legislature))

        return legislature

    def retrieve_legislators(self, url):
        html = BaseCollector.retrieve_uri(self, url, post_process=False, force_encoding='utf-8')
        return rows.import_from_html(BytesIO(html.encode('utf-8')), preserve_html=True)

    def retrieve_data_for_year(self, year):
        uri = 'http://www.senado.gov.br/transparencia/LAI/verba/{0}.csv'.format(year)
        self.debug(u'Downloading {0}'.format(uri))

        return BaseCollector.retrieve_uri(
            self, uri, force_encoding='windows-1252', post_process=False
        )

    def try_name_disambiguation(self, name):
        if name.title() == 'Luiz Henrique':
            mandates = Mandate.objects.filter(
                legislator__name=name.title(),
                legislature__date_start=self.legislature.date_start,
                legislature__institution=self.institution,
            )
            if mandates:
                return mandates[0].legislator, False
        return None, False

    def _get_or_create_legislator(self, name):
        legislator, created = self.try_name_disambiguation(name)
        if not legislator:
            legislator, created = Legislator.objects.get_or_create(name=name)
        if created:
            self.debug(u'New legislator: {0}'.format(legislator))
        else:
            self.debug(u'Found existing legislator: {0}'.format(legislator))
        return legislator

    def _update_legislators(self, legislators):
        for data in legislators:
            # Legislator
            name = extract_text(data.nome).replace('*', '').strip()
            legislator = self._get_or_create_legislator(name)
            email = None
            if hasattr(data, 'correio_eletronico'):
                email = data.correio_eletronico
                legislator.email = email
            site = extract_links(data.nome)[0]
            if site:
                legislator.site = site
            if site or email:
                legislator.save()
            self.debug(u'Updated legislator data: {0}'.format(legislator))

            # Mandate
            original_id = site.split('/')[-1]
            party, _ = PoliticalParty.objects.get_or_create(siglum=data.partido)
            mandate = self.mandate_for_legislator(
                legislator, party, data.uf, original_id
            )
            mandate.state = data.uf
            mandate.save()
            self.debug(u'Updated mandate data: {0}'.format(mandate))

    def update_legislators(self, data):
        legislators = self.retrieve_legislators(data.get('legislators'))
        self._update_legislators(legislators)
        if data.get('away_legislators'):
            away_legislators = self.retrieve_legislators(data.get('away_legislators'))
            self._update_legislators(away_legislators)

    def update_data(self):
        for data in self.legislature_data:
            self.legislature = self.get_legislature(data)
            self.update_legislators(data)
            self.collection_run = self.create_collection_run(self.legislature)
            for year in range(self.legislature.date_start.year, self.legislature.date_end.year + 1):
                self.update_data_for_year(year)

    def update_data_for_year(self, year):
        self.debug(u'Updating data for year {0}'.format(year))

        try:
            csv_data = self.retrieve_data_for_year(year).replace('\r\n', '\n')
        except Exception:
            print u'Not found data for year {0}'.format(year)
            return

        # Skip first line
        head, tail = csv_data.split('\n', 1)
        self.debug(u'Reading file...')
        data = rows.import_from_csv(BytesIO(tail.encode('utf-8')))

        if not data:
            self.debug(u'Error downloading file for year {0}'.format(year))
            return

        expected_header = [
            u'ano',
            u'mes',
            u'senador',
            u'tipo_despesa',
            u'cnpj_cpf',
            u'fornecedor',
            u'documento',
            u'data',
            u'detalhamento',
            u'valor_reembolsado',
        ]

        actual_header = data.fields.keys()

        if actual_header != expected_header:
            # FIXME
            print u'Bad CSV: expected header {0}, got {1}'.format(
                expected_header, actual_header
            )
            return

        archived_expense_list = []
        objects_counter = 0
        archived_expense_list_counter = len(data)

        legislators = {}
        mandates = {}
        natures = {}

        for row in data:
            if not row.senador:
                self.debug(u'Error downloading file for year {0}')
                continue

            if not row.data:
                date = '01/{0}/{1}'.format(row.mes, row.ano)
                expense_date = datetime.strptime(date, '%d/%m/%Y')
            else:
                expense_date = datetime.strptime(row.data, '%d/%m/%Y')

            name = self._normalize_name(row.senador)
            nature = row.tipo_despesa
            cpf_cnpj = row.cnpj_cpf
            supplier_name = row.fornecedor
            docnumber = row.documento
            expensed = row.valor_reembolsado

            # FIXME: WTF?
            if isinstance(expensed, unicode):
                expensed = float(expensed.replace(',', '.').replace('\r', '').replace('\n', ''))

            # memory cache
            expense_nature = natures.get(nature)
            if not expense_nature:
                expense_nature, _ = ExpenseNature.objects.get_or_create(name=nature)
                natures[nature] = expense_nature

            supplier = self.get_or_create_supplier(cpf_cnpj, supplier_name)

            # memory cache
            legislator = legislators.get(name)
            if not legislator:
                legislator = self._get_or_create_legislator(name)
                legislators[name] = legislator

            # memory cache
            mandate = mandates.get(name)
            if not mandate:
                mandate = self.mandate_for_legislator(legislator, None)
                mandates[name] = mandate

            expense = ArchivedExpense(
                number=docnumber,
                nature=expense_nature,
                date=expense_date,
                expensed=expensed,
                mandate=mandate,
                supplier=supplier,
                collection_run=self.collection_run
            )
            archived_expense_list.append(expense)
            self.debug(u'New expense found: {0}'.format(unicode(expense)))

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
