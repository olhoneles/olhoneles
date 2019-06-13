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

import json
import logging
import os
from datetime import date
from email.utils import formatdate as http_date
from zipfile import ZipFile

import requests
from dateutil import parser
from django.conf import settings

from montanha.mapping_institution import Institution
from montanha.mapping_expense import Expense
from montanha.mapping_collection_run import CollectionRun


logger = logging.getLogger(__name__)


class BaseCollector(object):

    def __init__(self, collection_runs, debug_enabled):
        self.debug_enabled = debug_enabled
        self.collection_runs = collection_runs
        self.collection_run = None

    def create_collection_run(
            self, institution_siglum, legislature_start, legislature_end):

        # FIXME
        if not CollectionRun._index.exists():
            CollectionRun.init()

        current_date = date.today().strftime('%F')
        collection_run, created = CollectionRun.get_or_create(
            date=current_date,
            institution_siglum=institution_siglum,
            legislature_year_start=legislature_start,
            legislature_year_end=legislature_end,
        )
        self.collection_runs.append(collection_run)

        # Keep only one run for a day. If one exists, we delete the existing
        # collection data before we start this one.
        if not created:
            logger.debug(
                'Collection run for {0} already exists for institution {1}, clearing.'.format(
                    current_date, institution_siglum
                )
            )
            self.remove_collection_run(collection_run, remove_run=False)

        return collection_run

    # FIXME
    def remove_collection_run(self, collection_run, remove_run=True):
        if remove_run:
            collection_run.delete()


class Collector(BaseCollector):

    def __init__(self, collection_runs, debug_enabled=False):
        super(Collector, self).__init__(collection_runs, debug_enabled)
        self.name = u'Câmara dos Deputados Federais'
        self.siglum = 'cdep'
        # FIXME
        self.collection_run = self.create_collection_run(self.siglum, 2015, 2018)

        if debug_enabled:
            logger.setLevel(logging.DEBUG)

        if not Institution._index.exists():
            Institution.init()

        # FIXME
        self.legislatures = [
            dict(date_start='2015-01-01', date_end='2018-12-31'),
            dict(date_start='2011-01-01', date_end='2014-12-31'),
            dict(date_start='2007-01-01', date_end='2010-12-31'),
        ]

        institution, _ = Institution.get_or_create(self.name, self.siglum)
        for x in self.legislatures:
            data_start = x.get('date_start')
            date_end = x.get('date_end')
            if not institution.has_legislature(data_start, date_end):
                institution.add_legislature(data_start, date_end)
                institution.save()

        # index for Expense and legislature
        expense_index = Expense._index.as_template('expenses')
        expense_index.save()
        # es = connections.get_connection()
        # es.indices.create(index='expenses-cdep-2015')


    def run(self):
        # self.update_legislators()
        self.update_data()

    # FIXME
    def parse_str(self, tag, text):
        if not text:
            return None
        elif tag == 'txtNumero':
            return u'{}'.format(text)
        elif tag == 'datEmissao':
            return parser.parse(text).isoformat()
        else:
            try:
                return float(text.replace(',', '.'))
            except Exception:
                return text

    def get_and_extract_json_files(self):
        data_path = os.path.join(os.getcwd(), 'data', 'cdep')
        if not os.path.isdir(data_path):
            os.makedirs(data_path)
            logger.debug(u'Creating directory {0}'.format(data_path))

        # FIXME: get year from legislature
        files_to_download = []
        for year in range(2018, 2017, -1):
            files_to_download.append('Ano-{0}.json.zip'.format(year))

        files_to_process = []
        for file_name in files_to_download:
            full_zip_file = os.path.join(data_path, file_name)
            json_file_name = file_name.replace('.zip', '')
            full_json_path = os.path.join(data_path, json_file_name)
            files_to_process.append(os.path.join(data_path, full_json_path))

            headers = {}
            if os.path.exists(full_zip_file):
                full_path = os.path.getmtime(full_zip_file)
                headers['If-Modified-Since'] = http_date(full_path, usegmt=True)

            uri = 'http://www.camara.leg.br/cotas/{0}'.format(file_name)
            logger.debug(u'Downloading {0}…'.format(uri))
            r = requests.get(uri, headers=headers, stream=True)

            if r.status_code == requests.codes.not_modified:
                logger.debug(
                    u'File {0} not updated since last download, skipping…'.format(
                        file_name
                    )
                )
                continue

            with open(full_json_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)

            logger.debug(u'Unzipping {0}…'.format(file_name))
            zf = ZipFile(full_zip_file, 'r')
            zf.extract(json_file_name, data_path)
        return files_to_process

    def _map_tags(self, tag):
        data = dict(
            # legislatura='legislature_year_start',
            ano='year',
            cnpjCPF='supplier_identifier',
            dataEmissao='date',
            descricao='nature',
            fornecedor='supplier_name',
            idDocumento='original_id',
            mes='month',
            nomeParlamentar='legislator',
            numeroDeputadoID='numero_deputado_id',
            siglaPartido='political_party_siglum',
            siglaUF='state_siglum',
            valorDocumento='document_value',
            valorLiquido='refund_value',
        )

        # ano
        # cnpjCPF
        # codigoLegislatura
        # dataEmissao
        # descricao
        # descricaoEspecificacao
        # fornecedor
        # idDocumento
        # legislatura
        # lote
        # mes
        # nomeParlamentar
        # numero
        # numeroCarteiraParlamentar
        # numeroDeputadoID
        # numeroEspecificacaoSubCota
        # numeroSubCota
        # parcela
        # passageiro
        # ressarcimento
        # restituicao
        # siglaPartido
        # siglaUF
        # tipoDocumento
        # trecho
        # valorDocumento
        # valorGlosa
        # valorLiquido

        return data.get(tag)

    def get_legislature(self, year):
        for x in self.legislatures:
            year_start = parser.parse(x.get('date_start')).year
            year_end = parser.parse(x.get('date_end')).year
            if year_start <= year <= year_end:
                return dict(year_start=year_start, year_end=year_end)
        return None

    def update_data(self):
        files_to_process = self.get_and_extract_json_files()
        for file_name in reversed(files_to_process):
            logger.debug(u"Processing {0}…".format(file_name))
            documents = []
            with open(file_name, 'r') as f:
                json_data = json.loads(f.read())
                expenses = json_data.get('dados', [])
                for json_expense in expenses:
                    expense = Expense()
                    expense.institution_siglum = self.siglum
                    expense.source = os.path.basename(file_name)
                    for x in json_expense.keys():
                        expense[self._map_tags(x)] = self.parse_str(x, json_expense[x])
                    legislature = self.get_legislature(int(expense.year))
                    expense.legislature_year_start = legislature.get('year_start')
                    expense.legislature_year_end = legislature.get('year_end')
                    documents.append(expense)

                    if len(documents) == settings.ES_OBJECT_LIST_MAXIMUM_COUNTER:
                        Expense.bulk_save(documents)
                        documents = []
                        logger.debug(
                            'Added {0} items'.format(
                                settings.ES_OBJECT_LIST_MAXIMUM_COUNTER
                            )
                        )
                if documents:
                    Expense.bulk_save(documents)
                    logger.debug('Added {0} items'.format(len(documents)))
                    documents = []

    """
    def retrieve_legislators(self):
        uri = 'http://www.camara.gov.br/SitCamaraWS/Deputados.asmx/ObterDeputados'
        return BaseCollector.retrieve_uri(self, uri)

    def update_legislators(self):
        xml = self.retrieve_legislators()

        for l in xml.findAll('deputado'):
            alternative_name = None
            name = l.find('nomeparlamentar')
            if not name:
                name = l.find('nome')
            else:
                alternative_name = l.find('nome').text.title().strip()

            name = name.text.title().strip()

            logger.debug(u"Looking for legislator: %s" % unicode(name))
            legislator, created = Legislator.objects.get_or_create(name=name)

            if created:
                logger.debug(u"New legislator: %s" % unicode(legislator))
            else:
                logger.debug(u"Found existing legislator: %s" % unicode(legislator))

            if alternative_name:
                try:
                    legislator.alternative_names.get(name=alternative_name)
                except AlternativeLegislatorName.DoesNotExist:
                    alternative_name, _ = AlternativeLegislatorName.objects.get_or_create(name=alternative_name)
                    legislator.alternative_name = alternative_name

            legislator.email = l.find('email').text
            legislator.save()

            party_name = self.normalize_party_name(l.find('partido').text)
            party, _ = PoliticalParty.objects.get_or_create(siglum=party_name)

            state = l.find('uf').text

            original_id = l.find('ideCadastro')

            self.mandate_for_legislator(legislator, party, state=state, original_id=original_id)
            """
