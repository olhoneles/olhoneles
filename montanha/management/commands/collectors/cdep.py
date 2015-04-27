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

import os
import requests
import subprocess
from datetime import date, datetime
from django.db import reset_queries
from email.utils import formatdate as http_date
from basecollector import BaseCollector
from lxml.etree import iterparse
from montanha.models import (ArchivedExpense, Institution, Legislature,
                             Legislator, AlternativeLegislatorName, Mandate,
                             ExpenseNature, Supplier, PoliticalParty, CollectionRun)
from zipfile import ZipFile


OBJECT_LIST_MAXIMUM_COUNTER = 1000


class CamaraDosDeputados(BaseCollector):
    def __init__(self, collection_runs, debug_enabled=False):
        super(CamaraDosDeputados, self).__init__(collection_runs, debug_enabled)

        institution, _ = Institution.objects.get_or_create(siglum='CDF', name=u'Câmara dos Deputados Federais')
        self.legislature, _ = Legislature.objects.get_or_create(institution=institution,
                                                                date_start=datetime(2015, 1, 1),
                                                                date_end=datetime(2018, 12, 31))

    def retrieve_legislators(self):
        uri = 'http://www.camara.gov.br/SitCamaraWS/Deputados.asmx/ObterDeputados'
        return BaseCollector.retrieve_uri(self, uri)

    def try_name_disambiguation(self, name):
        if name.title() == 'Sergio Souza':
            return Legislator.objects.get(id=293), False

        return None, False

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

            self.debug(u"Looking for legislator: %s" % unicode(name))
            legislator, created = Legislator.objects.get_or_create(name=name)

            if created:
                self.debug(u"New legislator: %s" % unicode(legislator))
            else:
                self.debug(u"Found existing legislator: %s" % unicode(legislator))

            if alternative_name:
                try:
                    legislator.alternative_names.get(name=alternative_name)
                except AlternativeLegislatorName.DoesNotExist:
                    alternative_name, _ = AlternativeLegislatorName.objects.get_or_create(name=alternative_name)
                    legislator.alternative_name = alternative_name

            legislator.email = l.find('email').text
            legislator.save()

            party_name = self._normalize_party_name(l.find('partido').text)
            party, _ = PoliticalParty.objects.get_or_create(siglum=party_name)

            state = l.find('uf').text

            original_id = l.find('ideCadastro')

            mandate = self.mandate_for_legislator(legislator, party,
                                                  state=state, original_id=original_id)

    def update_data(self):
        if os.path.exists('cdep-collection-run'):
            crid = int(open('cdep-collection-run').read())
            CollectionRun.objects.get(id=crid).delete()
            os.unlink('cdep-collection-run')

        self.collection_run = self.create_collection_run(self.legislature)

        data_path = os.path.join(os.getcwd(), 'data', 'cdep')

        files_to_download = ['AnoAtual.zip']
        previous_years = date.today().year - self.legislature.date_start.year

        if previous_years:
            files_to_download.append('AnoAnterior.zip')

        if previous_years > 1:
            files_to_download.append('AnosAnteriores.zip')

        files_to_process = list()
        for file_name in files_to_download:
            xml_file_name = file_name.replace('zip', 'xml')
            full_xml_path = os.path.join(data_path, xml_file_name)
            files_to_process.append(os.path.join(data_path, full_xml_path))

            full_path = os.path.join(data_path, file_name)

            headers = dict()
            if os.path.exists(full_path):
                headers['If-Modified-Since'] = http_date(os.path.getmtime(full_path), usegmt=True)

            uri = 'http://www.camara.gov.br/cotas/' + file_name
            self.debug(u"Preparing to download %s…" % (uri))
            r = requests.get(uri, headers=headers, stream=True)

            if r.status_code == requests.codes.not_modified:
                self.debug(u"File %s not updated since last download, skipping…" % file_name)
                continue

            with open(full_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)

            self.debug(u"Unzipping %s…" % (file_name))
            zf = ZipFile(full_path, 'r')
            zf.extract(xml_file_name, data_path)

        open('cdep-collection-run', 'w').write('%d' % (self.collection_run.id))
        archived_expense_list = []
        for file_name in reversed(files_to_process):
            self.debug(u"Processing %s…" % file_name)
            objects_counter = 0

            context = iterparse(file_name, events=("start", "end"))

            # turn it into an iterator
            context = iter(context)

            for event, elem in context:
                if event != "end" or elem.tag != "DESPESA":
                    continue

                # Some entries lack numLegislatura, so we fallback to numAno.
                legislature_year = elem.find('nuLegislatura')
                if legislature_year is not None:
                    legislature_year = int(legislature_year.text)
                else:
                    legislature_year = int(elem.find('numAno').text)
                    if legislature_year < self.legislature.date_start.year or \
                       legislature_year > self.legislature.date_end.year:
                        legislature_year = None
                    else:
                        legislature_year = self.legislature.date_start.year

                if legislature_year != self.legislature.date_start.year:
                    self.debug(u"Ignoring entry because it's out of the target legislature…")
                    continue

                name = elem.find('txNomeParlamentar').text.title().strip()

                nature = elem.find('txtDescricao').text.title().strip()

                supplier_name = elem.find('txtBeneficiario')
                if supplier_name is not None:
                    supplier_name = supplier_name.text.title().strip()
                else:
                    supplier_name = u'Sem nome'

                supplier_identifier = elem.find('txtCNPJCPF')
                if supplier_identifier is not None and supplier_identifier.text is not None:
                    supplier_identifier = self.normalize_cnpj_or_cpf(supplier_identifier.text)

                if not supplier_identifier:
                    supplier_identifier = u'Sem CNPJ/CPF (%s)' % supplier_name

                try:
                    supplier = Supplier.objects.get(identifier=supplier_identifier)
                except Supplier.DoesNotExist:
                    supplier = Supplier(identifier=supplier_identifier, name=supplier_name)
                    supplier.save()

                docnumber = elem.find('txtNumero').text
                if docnumber:
                    docnumber = docnumber.strip()

                expense_date = elem.find('datEmissao')
                if expense_date is not None:
                    expense_date = date(*((int(x.lstrip('0')) for x in expense_date.text[:10].split('-'))))
                else:
                    expense_year = int(elem.find('numAno').text)
                    expense_month = int(elem.find('numMes').text)
                    expense_date = date(expense_year, expense_month, 1)

                expensed = float(elem.find('vlrLiquido').text)

                nature, _ = ExpenseNature.objects.get_or_create(name=nature)

                party = party_name = elem.find('sgPartido')
                if party_name is not None:
                    party_name = self._normalize_party_name(party_name.text)
                    party, _ = PoliticalParty.objects.get_or_create(siglum=party_name)

                state = elem.find('sgUF').text.strip()

                original_id = elem.find('ideCadastro').text.strip()

                try:
                    legislator = Legislator.objects.get(name__iexact=name)
                except Legislator.DoesNotExist:
                    # Some legislators do are not listed in the other WS because they are not
                    # in exercise.
                    self.debug(u"Found legislator who's not in exercise: %s" % name)
                    legislator = Legislator(name=name)
                    legislator.save()
                mandate = self.mandate_for_legislator(legislator, party,
                                                      state=state, original_id=original_id)
                expense = ArchivedExpense(number=docnumber,
                                          nature=nature,
                                          date=expense_date,
                                          expensed=expensed,
                                          mandate=mandate,
                                          supplier=supplier,
                                          collection_run=self.collection_run)
                archived_expense_list.append(expense)
                self.debug(u"New expense found: %s" % unicode(expense))

                objects_counter += 1

                if objects_counter == OBJECT_LIST_MAXIMUM_COUNTER:
                    ArchivedExpense.objects.bulk_create(archived_expense_list)
                    archived_expense_list[:] = []
                    objects_counter = 0
                    reset_queries()

                elem.clear()
                while elem.getprevious() is not None:
                    del elem.getparent()[0]

                continue

        if archived_expense_list:
            ArchivedExpense.objects.bulk_create(archived_expense_list)

        os.unlink('cdep-collection-run')

    def _normalize_name(self, name):
        names_map = {
            'Gim': 'Gim Argello',
        }
        return names_map.get(name, name)
