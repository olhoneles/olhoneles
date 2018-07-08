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

import threading
import time
from datetime import datetime, date

from basecollector import BaseCollector
from montanha.models import (
    Institution, Legislature, ExpenseNature, Legislator, ArchivedExpense
)


def parse_money(string):
    string = string.strip('R$ ')
    string = string.replace('.', '')
    string = string.replace(',', '.')
    return float(string)


def parse_date(string):
    return datetime.strptime(string, '%d/%m/%Y').date()


NUM_THREADS = 6
MAX_PENDING = 100


class Collector(BaseCollector):
    def __init__(self, collection_runs, debug_enabled=False):
        super(Collector, self).__init__(collection_runs, debug_enabled)

        self.institution, _ = Institution.objects.get_or_create(
            siglum='CMBH', name=u'Câmara Municipal de Belo Horizonte'
        )

        self.legislature, _ = Legislature.objects.get_or_create(
            institution=self.institution,
            date_start=datetime(2013, 1, 1),
            date_end=datetime(2016, 12, 31)
        )

        self.download_threads = []
        for x in range(NUM_THREADS):
            thread = threading.Thread(target=self._download_thread)
            thread.daemon = True
            self.download_threads.append(thread)

        self.download_queue = []
        self.download_lock = threading.Lock()

        self.processing_queue = []
        self.processing_condition = threading.Condition()

    def run(self):
        self.update_legislators()
        self.update_data()

    def _download_thread(self):
        throttle = False
        while True:
            args = []

            if throttle:
                throttle = False
                time.sleep(15)

            with self.download_lock:
                if not self.download_queue:
                    break

                args += self.download_queue.pop(0)

            assert len(args) == 3

            data = self.retrieve_actual_data(*args)

            with self.processing_condition:
                self.processing_queue.append([data] + args)
                self.processing_condition.notify()

                if len(self.processing_queue) > MAX_PENDING:
                    throttle = True

    def _is_done_downloading(self):
        for thread in self.download_threads:
            if thread.is_alive():
                return False
        return True

    def retrieve_month(self, month, year):
        uri = 'https://www.cmbh.mg.gov.br/transparencia/vereadores/verba-indenizatoria'
        data = {'codVereadorVI': '', 'mes': '{:0>2}'.format(month), 'ano': year}
        headers = {
            'Origin': 'https://www.cmbh.mg.gov.br',
            'Referer': 'https://www.cmbh.mg.gov.br/transparencia/verba-indenizatoria',
        }
        return BaseCollector.retrieve_uri(self, uri, data, headers)

    def retrieve_actual_data(self, code, month, year):
        uri = 'https://www.cmbh.mg.gov.br/transparencia/vereadores/verba-indenizatoria'
        data = {'codVereadorVI': '', 'mes': '{:0>2}'.format(month), 'ano': year, 'vereador': code}
        headers = {
            'Origin': 'https://www.cmbh.mg.gov.br',
            'Referer': 'https://www.cmbh.mg.gov.br/transparencia/verba-indenizatoria',
        }
        return BaseCollector.retrieve_uri(self, uri, data, headers)

    def update_legislators(self):
        pass

    def _normalize_nature(self, nature):
        if not hasattr(self, 'nature_map'):
            self.nature_map = {
                'Servico ou Produto Postal': u'Serviço ou Produto Postal',
                'Periodico': 'Periódico',
                'Material de Escritorio': u'Material de Escritório',
                'Material de Informatica': u'Material de Informática',
                'Servico de Escritorio': u'Serviço de Escritório',
                'Servico de Informatica': u'Serviço de Informática',
                'Estacionamento': u'Estacionamento',
                'Lanche': u'Lanche',
                'Refeic?o': u'Refeição',
                'Telecomunicac?o': u'Telecomunicação',
                'Combustivel': u'Combustível',
                'Manutenc?o e Locac?o de Veiculo': u'Manutenção e Locação de Veículo',
                'Participac?o em Curso ou Seminario': u'Participação em Curso ou Seminário',
                'Viagem a Servico': u'Viagem a Serviço',
                'Consultoria Tecnico-Especializada': u'Consultoria Técnico-Especializada',
                'Apoio a Promoc?o de Eventos Oficiais': u'Apoio a Promoção de Eventos Oficiais',
                'Escritorio Representac?o Parlamentar': u'Escritório Representação Parlamentar',
                'Servico Grafico': u'Serviço Gráfico',
                'Divulgac?o de Atividade Parlamentar': u'Divulgação de Atividade Parlamentar'
            }

        return self.nature_map.get(nature, nature)

    def download_data(self, code, month, year):
        self.download_queue.append([code, month, year])

    def update_data_for_legislator(self, data, code, month, year):
        self.debug("Updating data %s/%s for legislator: %s" % (month, year, code))

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
            nature, _ = ExpenseNature.objects.get_or_create(name=self._normalize_nature(data.text))
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

                supplier = self.get_or_create_supplier(cnpj, supplier_name)

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
        for year in range(self.legislature.date_start.year, self.legislature.date_end.year + 1):
            self.update_data_for_year(year)

        for thread in self.download_threads:
            thread.start()

        while True:
            args = []

            done_downloading = self._is_done_downloading()
            with self.processing_condition:
                self.debug("Left to process: %d Done downloading?: %d" % (
                    len(self.processing_queue),
                    done_downloading)
                )
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
