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
import threading
from basecollector import BaseCollector
from datetime import datetime, date
from montanha.models import (
    Institution, Legislature, ExpenseNature, Legislator, Supplier,
    ArchivedExpense
)


def parse_money(string):
    string = string.strip('R$ ')
    string = string.replace('.', '')
    string = string.replace(',', '.')
    return float(string)


def parse_date(string):
    return datetime.strptime(string, '%d/%m/%Y').date()


NUM_THREADS = 12


class CMBH(BaseCollector):
    def __init__(self, collection_runs, debug_enabled=False):
        super(CMBH, self).__init__(collection_runs, debug_enabled)

        try:
            institution = Institution.objects.get(siglum='CMBH')
        except Institution.DoesNotExist:
            institution = Institution(siglum='CMBH', name=u'Câmara Municipal de Belo Horizonte')
            institution.save()

        try:
            self.legislature = Legislature.objects.all().filter(institution=institution).order_by('-date_start')[0]
        except IndexError:
            self.legislature = Legislature(institution=institution,
                                           date_start=datetime(2013, 1, 1),
                                           date_end=datetime(2016, 12, 31))
            self.legislature.save()

        self.download_threads = []
        for x in range(NUM_THREADS):
            thread = threading.Thread(target=self._download_thread)
            thread.daemon = True
            self.download_threads.append(thread)

        self.download_queue = []
        self.download_lock = threading.Lock()

        self.processing_queue = []
        self.processing_condition = threading.Condition()

    def _download_thread(self):
        while True:
            args = []
            with self.download_lock:
                if not self.download_queue:
                    break
                args += self.download_queue.pop(0)
            assert len(args) == 3

            data = self.retrieve_actual_data(*args)

            with self.processing_condition:
                self.processing_queue.append([data] + args)
                self.processing_condition.notify()

    def _is_done_downloading(self):
        for thread in self.download_threads:
            if thread.is_alive():
                return False
        return True

    def retrieve_month(self, month, year):
        uri = 'http://www.cmbh.mg.gov.br/transparencia/verba-indenizatoria'
        data = {'codVereadorVI': '', 'mes': '{:0>2}'.format(month), 'ano': year}
        headers = {
            'Origin': 'http://www.cmbh.mg.gov.br',
            'Referer': 'http://www.cmbh.mg.gov.br/transparencia/verba-indenizatoria',
        }
        return BaseCollector.retrieve_uri(self, uri, data, headers)

    def retrieve_actual_data(self, code, month, year):
        uri = 'http://www.cmbh.mg.gov.br/transparencia/verba-indenizatoria'
        data = {'codVereadorVI': '', 'mes': '{:0>2}'.format(month), 'ano': year, 'vereador': code}
        headers = {
            'Origin': 'http://www.cmbh.mg.gov.br',
            'Referer': 'http://www.cmbh.mg.gov.br/transparencia/verba-indenizatoria',
        }
        return BaseCollector.retrieve_uri(self, uri, data, headers)

    def update_legislators(self):
        pass

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
                'Refeic?o': 'Refeicão',
                'Telecomunicac?o': 'Telecomunicação',
                'Combustivel': 'Combustivel',
                'Manutenc?o e Locac?o de Veiculo': 'Manutenção e Locação de Veiculo',
                'Participac?o em Curso ou Seminario': 'Participação em Curso ou Seminario',
                'Viagem a Servico': 'Viagem a Serviço',
                'Consultoria Tecnico-Especializada': 'Consultoria Técnico-Especializada',
                'Apoio a Promoc?o de Eventos Oficiais': 'Apoio a Promoção de Eventos Oficiais',
                'Escritorio Representac?o Parlamentar': 'Escritorio Representação Parlamentar',
                'Servico Grafico': 'Serviço Gráfico',
                'Divulgac?o de Atividade Parlamentar': 'Divulgação de Atividade Parlamentar'
            }

        return self.nature_map.get(nature, nature)

    def download_data(self, code, month, year):
        self.download_queue.append([code, month, year])

    def update_data_for_legislator(self, data, code, month, year):
        data = data.find('div', {'class': 'row'})

        legislator = data.find('h2').findChildren()[0].next
        legislator = self._normalize_name(legislator)
        legislator, created = Legislator.objects.get_or_create(name=legislator)

        if created:
            self.debug("New legislator: %s" % unicode(legislator))
        else:
            self.debug("Found existing legislator: %s" % unicode(legislator))

        mandate = self.mandate_for_legislator(legislator, party=None, original_id=code)

        natures = data.findAll('h3')
        for data in natures:
            nature = self._normalize_nature(data.text)
            try:
                nature = ExpenseNature.objects.get(name=nature)
            except ExpenseNature.DoesNotExist:
                nature = ExpenseNature(name=nature)
                nature.save()

            rows = data.findNext().findAll('tr')[1:-1]
            for row in rows:
                columns = row.findAll('td')

                if not len(columns) == 5:
                    print u'Bad row: %s' % unicode(columns)
                    continue

                cnpj = self.normalize_cnpj_or_cpf(columns[0].getText())

                supplier_name = columns[1].getText().strip()

                try:
                    supplier_name = supplier_name.decode('utf-8')
                except Exception:
                    pass

                try:
                    supplier = Supplier.objects.get(identifier=cnpj)
                except Supplier.DoesNotExist:
                    supplier = Supplier(identifier=cnpj, name=supplier_name)
                    supplier.save()

                docnumber = columns[2].getText()
                expensed = parse_money(columns[3].getText())

                expense = ArchivedExpense(number=docnumber,
                                          nature=nature,
                                          date=date(year, month, 1),
                                          expensed=expensed,
                                          mandate=mandate,
                                          supplier=supplier,
                                          collection_run=self.collection_run)
                expense.save()

                self.debug("New expense found: %s" % unicode(expense))

    def update_data(self):
        self.collection_run = self.create_collection_run(self.legislature)
        for year in range(self.legislature.date_start.year, datetime.now().year + 1):
            self.update_data_for_year(year)

        for thread in self.download_threads:
            thread.start()

        while True:
            args = []

            done_downloading = self._is_done_downloading()
            with self.processing_condition:
                self.debug("Left to process: %d Done downloading?: %d" % (len(self.processing_queue), done_downloading))
                if not self.processing_queue:
                    if done_downloading:
                        break
                    self.processing_condition.wait(0.1)
                    continue
                args += self.processing_queue.pop(0)

            if not args:
                continue

            assert len(args) == 4
            self.update_data_for_legislator(*args)

        for thread in self.download_threads:
            thread.join()
        self.download_threads = []

    def update_data_for_year(self, year=datetime.now().year):
        for month in range(1, 13):
            data = self.retrieve_month(month, year)
            data = data.find('table')
            anchors = data.findAll('a')
            for anchor in anchors:
                parts = anchor['onclick'].split("'")
                code = parts[3]
                self.download_data(code, month, year)
