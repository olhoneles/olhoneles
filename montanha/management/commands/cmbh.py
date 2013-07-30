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
from basecollector import BaseCollector
from datetime import datetime, date
from montanha.models import *


def parse_money(string):
    string = string.strip('R$ ')
    string = string.replace('.', '')
    string = string.replace(',', '.')
    return float(string)


def parse_date(string):
    return datetime.strptime(string, '%d/%m/%Y').date()


def parse_cmbh_date(date_string):
    day = '01'
    month, year = date_string.split('/')
    return parse_date(day + '/' + month + '/' + year)


class CMBH(BaseCollector):
    def __init__(self, debug_enabled=False, full_scan=False):
        self.debug_enabled = debug_enabled
        self.full_scan = full_scan
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

    def retrieve_months(self):
        uri = 'http://www.cmbh.mg.gov.br/extras/verba_indenizatoria_nota_fiscal/lista_meses.php'
        data = {'tipo': 'd'}
        headers = {
            'Referer': 'http://www.cmbh.mg.gov.br/extras/verba_indenizatoria_nota_fiscal/index.php',
            'Origin': 'http://www.cmbh.mg.gov.br',
        }
        return BaseCollector.retrieve_uri(self, uri, data, headers)

    def retrieve_legislators(self, month):
        uri = 'http://www.cmbh.mg.gov.br/extras/verba_indenizatoria_nota_fiscal/oracle_lista_vereadores.php'
        data = {'mes': month}
        headers = {
            'Referer': 'http://www.cmbh.mg.gov.br/extras/verba_indenizatoria_nota_fiscal/lista_meses.php',
            'Origin': 'http://www.cmbh.mg.gov.br',
        }
        return BaseCollector.retrieve_uri(self, uri, data, headers)

    def retrieve_expense_types(self, month, legislator, code):
        uri = 'http://www.cmbh.mg.gov.br/extras/verba_indenizatoria_nota_fiscal/oracle_lista_tipodespesa.php'
        data = {'mes': month, 'vereador': legislator, 'cod': code}
        headers = {
            'Referer': 'http://www.cmbh.mg.gov.br/extras/verba_indenizatoria_nota_fiscal/oracle_lista_vereadores.php',
            'Origin': 'http://www.cmbh.mg.gov.br',
        }
        return BaseCollector.retrieve_uri(self, uri, data, headers)

    def retrieve_actual_data(self, code, seq, legislator, nature, month):
        uri = 'http://www.cmbh.mg.gov.br/extras/verba_indenizatoria_nota_fiscal/oracle_lista_valordespesa.php'
        data = {
            'cod': code,
            'seq': seq,
            'vereador': legislator,
            'tipodespesa': nature,
            'mes': month
        }
        headers = {
            'Referer': 'http://www.cmbh.mg.gov.br/extras/verba_indenizatoria_nota_fiscal/oracle_lista_tipodespesa.php',
            'Origin': 'http://www.cmbh.mg.gov.br',
        }
        return BaseCollector.retrieve_uri(self, uri, data, headers)

    def update_legislators(self):
        pass

    def update_data_for_legislator(self, month, legislator, code):
        expense_types = self.retrieve_expense_types(month, legislator, code)

        if not expense_types:
            return

        # Ignore the last one, which is the total.
        expense_types = expense_types.find('ul').findAll('a')[:-1]

        parameters_list = []
        for etype in expense_types:
            parts = etype['onclick'].split("'")
            legislator = parts[1]
            code = parts[3]
            nature = parts[5]
            seq = parts[7]
            month = parts[9]

            data = self.retrieve_actual_data(code, seq, legislator, nature, month)

            if not data:
                print 'No data...'
                continue

            # Get the lines of data, ignoring the first one, which
            # contains the titles, and the last one, which contains
            # the total.
            data = data.find('div', 'texto_valores1').findAll('tr')[1:-1]

            if not data:
                continue

            legislator = base64.decodestring(legislator).strip().decode('utf-8')
            date = parse_cmbh_date(base64.decodestring(month).strip().decode('utf-8'))

            nature = base64.decodestring(nature).strip().decode('utf-8')
            try:
                nature = ExpenseNature.objects.get(name=nature)
            except ExpenseNature.DoesNotExist:
                nature = ExpenseNature(name=nature)
                nature.save()

            try:
                legislator = Legislator.objects.get(original_id=code)
                self.debug("Found existing legislator: %s" % unicode(legislator))

                mandate = self.mandate_for_legislator(legislator, None)
            except Legislator.DoesNotExist:
                legislator = Legislator(name=legislator, original_id=code)
                legislator.save()

                mandate = Mandate(legislator=legislator, date_start=self.legislature.date_start, party=None, legislature=self.legislature)
                mandate.save()

                self.debug("New legislator found: %s" % unicode(legislator))

            for row in data:
                columns = row.findAll('td')

                if not len(columns) == 5:
                    print u'Bad row: %s' % unicode(columns)
                    continue

                cnpj = columns[0].getText().replace('.', '').replace('-', '').replace('/', '').strip()

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

                try:
                    expense = Expense.objects.get(number=docnumber,
                                                  nature=nature,
                                                  date=date,
                                                  expensed=expensed,
                                                  mandate=mandate,
                                                  supplier=supplier)
                    self.debug("Existing expense found: %s" % unicode(expense))
                except Expense.DoesNotExist:
                    expense = Expense(number=docnumber,
                                      nature=nature,
                                      date=date,
                                      expensed=expensed,
                                      mandate=mandate,
                                      supplier=supplier)
                    expense.save()

                    self.debug("New expense found: %s" % unicode(expense))

    def update_data(self):
        if self.full_scan:
            for year in range(self.legislature.date_start.year, datetime.now().year + 1):
                self.update_data_for_year(year)
        else:
            self.update_data_for_year(datetime.now().year)

    def update_data_for_year(self, year=datetime.now().year):
        self.debug("Updating data for year %d" % year)
        months = self.retrieve_months().findAll('div', 'arquivo_meses')

        date_list = []
        for month in months:
            anchor = month.find('a')
            parts = anchor['onclick'].split("'")
            date_list.append(parts[1])

        for date in date_list:
            leg_list = self.retrieve_legislators(date)
            anchors = leg_list.find('ul').findAll('a')
            for anchor in anchors:
                parts = anchor['onclick'].split("'")
                legislator = parts[1]
                code = parts[3]
                month = parts[5]
                self.update_data_for_legislator(month, legislator, code)
