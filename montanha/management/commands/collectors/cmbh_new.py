# -*- coding: utf-8 -*-
#
# Copyright (©) 2010-2013 Estêvão Samuel Procópio
# Copyright (©) 2010-2013 Gustavo Noronha Silva
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

import csv
import json
from datetime import datetime, date
from io import BytesIO

import rows

from basecollector import BaseCollector
from montanha.models import (
    ArchivedExpense, ExpenseNature, Institution, Legislator, Legislature,
    PoliticalParty, Supplier
)


def parse_money(string):
    string = string.strip('R$ ')
    string = string.replace('.', '')
    string = string.replace(',', '.')
    return float(string)


class CMBH(BaseCollector):

    def __init__(self, collection_runs, debug_enabled=False):
        super(CMBH, self).__init__(collection_runs, debug_enabled)

        # FIXME
        # self.current_legislators_details = self.current_legislators_details()

        self.institution, _ = Institution.objects.get_or_create(
            siglum='CMBH', name=u'Câmara Municipal de Belo Horizonte'
        )
        self.legislature = None
        self.legislature_data = [
            {
                'start': 2008,
                'end': 2011,
            },
            {
                'start': 2012,
                'end': 2015,
            },
            {
                'start': 2013,
                'end': 2016,
            },
            {
                'start': 2017,
                'end': 2020,
            },
        ]

    def _normalize_nature(self, nature):
        if not hasattr(self, 'nature_map'):
            self.nature_map = {
                'Servico ou Produto Postal': 'Serviço ou Produto Postal',
                'Periodico': 'Periódico',
                'Material de Escritorio': 'Material de Escritório',
                'Material de Informatica': 'Material de Informática',
                'Servico de Escritorio': 'Serviço de Escritório',
                'Servico de Informatica': 'Serviço de Informática',
                'Estacionamento': 'Estacionamento',
                'Lanche': 'Lanche',
                'Refeic?o': 'Refeição',
                'Telecomunicac?o': 'Telecomunicação',
                'Combustivel': 'Combustível',
                'Manutenc?o e Locac?o de Veiculo': 'Manutenção e Locação de Veículo',
                'Participac?o em Curso ou Seminario': 'Participação em Curso ou Seminário',
                'Viagem a Servico': 'Viagem a Serviço',
                'Consultoria Tecnico-Especializada': 'Consultoria Técnico-Especializada',
                'Apoio a Promoc?o de Eventos Oficiais': 'Apoio a Promoção de Eventos Oficiais',
                'Escritorio Representac?o Parlamentar': 'Escritório Representação Parlamentar',
                'Servico Grafico': 'Serviço Gráfico',
                'Divulgac?o de Atividade Parlamentar': 'Divulgação de Atividade Parlamentar'
            }

        return self.nature_map.get(nature, nature)

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

    # FIXME
    def current_legislators_details(self):
        legislators = {}
        url = 'https://www.cmbh.mg.gov.br/vereadores'
        html = BaseCollector.retrieve_uri(self, url, force_encoding='utf-8')
        divs = html.findAll('div', attrs={'class': 'vereador'})
        for div in divs:
            name = div.find('div', attrs={'class': 'views-field views-field-title'}).text
            legislators[name] = {
                'party': div.find('div', attrs={'class': 'views-field views-field-field-sigla'}).text,
                'picture': div.find('img').get('src')
            }
        return legislators

    def update_data(self):
        for data in self.legislature_data:
            self.legislature = self.get_legislature(data)
            self.collection_run = self.create_collection_run(self.legislature)
            for year in range(self.legislature.date_start.year, self.legislature.date_end.year + 1):
                self.update_data_for_year(year)

    def retrieve_legislator_data(self, name):
        url = '{0}/?{1}&{2}&name__in={3}'.format(
            'http://politicos.olhoneles.org/api/v0/politicians',
            'candidacies__city__name__in=Belo+Horizonte',
            'candidacies__political_office__slug__in=vereador',
            name,
        )
        data = BaseCollector.retrieve_uri(self, url, force_encoding='utf-8', post_process=False)
        return json.loads(data)

    def retrieve_legislator_csv(self, year, month, legislator):
        url = '{0}_{1}-{2}_{3}.csv'.format(
            'http://www.cmbh.mg.gov.br:9001/verba_indenizatoria',
            legislator,
            month,
            year,
        )
        self.debug(u'Downloading {0}'.format(url))

        return BaseCollector.retrieve_uri(self, url, force_encoding='utf-8', post_process=False)

    def retrieve_legislators(self, year):
        uri = 'http://www.cmbh.mg.gov.br/transparencia/verba-indenizatoria'
        data = {'ano': year}
        headers = {
            'Origin': 'http://www.cmbh.mg.gov.br',
            'Referer': 'http://www.cmbh.mg.gov.br/transparencia/verba-indenizatoria',
        }
        return BaseCollector.retrieve_uri(self, uri, data, headers, post_process=False)

    def update_data_for_year(self, year):
        # there is no data before 2013
        if year < 2013 or year > datetime.now().year:
            return

        self.debug(u'Updating data for year {0}'.format(year))

        html = self.retrieve_legislators(year).encode('utf-8')
        legislators = rows.import_from_html(BytesIO(html), preserve_html=True)

        for month in range(1, 13):
            for legislator in legislators:
                self.update_data_for_month(legislator, year, month)

    def _get_political_party(self, political_parties, legislature):
        if len(political_parties) == 1:
            return political_parties[0]
        for political_party in political_parties:
            if political_party["date_start"] >= legislature.date_start.year and \
                    (political_party["date_end"] <= legislature.date_end.year or political_party["date_end"] is None):
                return political_party.get('political_party', {})
        return None

    def update_data_for_month(self, legislator, year, month):
        self.debug(u'Updating data for month {0}'.format(month))

        slug = legislator.vereador.replace(' ', '_')
        name = legislator.vereador

        try:
            csv_data = self.retrieve_legislator_csv(year, str(month).zfill(2), slug)
        except Exception:
            print u'Not found data for year {0}'.format(year)
            return

        legislator, created = Legislator.objects.get_or_create(name=name)
        if created:
            self.debug(u'New legislator: {0}'.format(legislator))
        else:
            self.debug(u'Found existing legislator: {0}'.format(legislator))

        # FIXME
        legislator_data = self.retrieve_legislator_data(legislator.name)
        party = None
        if legislator_data.get('objects'):
            api_objects = legislator_data.get('objects')[0]
            political_parties = api_objects.get('political_parties', {})
            party_party = self._get_political_party(political_parties, self.legislature)
            party_siglum = party_party.get('siglum')
            party, _ = PoliticalParty.objects.get_or_create(siglum=party_siglum)
        mandate = self.mandate_for_legislator(legislator, party=party, original_id=None)
        if party and mandate.party is None:
            mandate.party = party
            mandate.save()
            self.debug(u'Updated mandate data: {0}'.format(mandate))

        # data = rows.import_from_csv(BytesIO(csv_data.encode('utf-8')), preserve_html=True)
        reader = csv.DictReader(BytesIO(csv_data.encode('utf-8')), delimiter=';')
        for data in reader:
            nature = data.get('CATEGORIA')
            if nature is None:
                continue

            nature = self._normalize_nature(nature)
            expense_nature, _ = ExpenseNature.objects.get_or_create(name=nature)

            cpf_cnpj = data.get('CNPJ/CPF')
            supplier_name = data.get('FORNECEDOR')
            docnumber = data.get('NUMERO DOCUMENTO')
            expensed = data.get('VALOR INDENIZADO')

            if supplier_name is None or expensed is None:
                continue

            supplier, _ = Supplier.objects.get_or_create(
                identifier=cpf_cnpj,
                name=supplier_name
            )

            expense = ArchivedExpense(
                number=docnumber,
                nature=expense_nature,
                date=date(year, month, 1),
                expensed=parse_money(expensed),
                mandate=mandate,
                supplier=supplier,
                collection_run=self.collection_run
            )
            expense.save()

            self.debug(u'New expense found: {0}'.format(expense))
