# -*- coding: utf-8 -*-
from basesource import *
from cmbh.models import Legislator, Supplier, Expense
from cmbh import models

import base64


Session = models.initialize(get_database_path('cmbh'))


def parse_cmbh_date(date_string):
    day = '01'
    month, year = date_string.split('/')
    return parse_date(day + '/' + month + '/' + year)


class VerbaIndenizatoriaCMBH(BaseCollector):

    def retrieve_months(self):
        uri  = 'http://www.cmbh.mg.gov.br/extras/verba_indenizatoria_nota_fiscal/lista_meses.php'
        data = { 'tipo' : 'd' }
        headers = {
            'Referer' : 'http://www.cmbh.mg.gov.br/extras/verba_indenizatoria_nota_fiscal/index.php',
            'Origin' : 'http://www.cmbh.mg.gov.br',
            }
        return BaseCollector.retrieve_uri(self, uri, data, headers)

    def retrieve_legislators(self, month):
        uri  = 'http://www.cmbh.mg.gov.br/extras/verba_indenizatoria_nota_fiscal/oracle_lista_vereadores.php'
        data = { 'mes' : month }
        headers = {
            'Referer' : 'http://www.cmbh.mg.gov.br/extras/verba_indenizatoria_nota_fiscal/lista_meses.php',
            'Origin' : 'http://www.cmbh.mg.gov.br',
            }
        return BaseCollector.retrieve_uri(self, uri, data, headers)

    def retrieve_expense_types(self, month, legislator, code):
        uri  = 'http://www.cmbh.mg.gov.br/extras/verba_indenizatoria_nota_fiscal/oracle_lista_tipodespesa.php'
        data = { 'mes' : month, 'vereador': legislator, 'cod' : code }
        headers = {
            'Referer' : 'http://www.cmbh.mg.gov.br/extras/verba_indenizatoria_nota_fiscal/oracle_lista_vereadores.php',
            'Origin' : 'http://www.cmbh.mg.gov.br',
            }
        return BaseCollector.retrieve_uri(self, uri, data, headers)

    def retrieve_actual_data(self, code, seq, legislator, nature, month):
        uri  = 'http://www.cmbh.mg.gov.br/extras/verba_indenizatoria_nota_fiscal/oracle_lista_valordespesa.php'
        data = {
            'cod' : code,
            'seq' : seq,
            'vereador': legislator,
            'tipodespesa' : nature,
            'mes' : month
            }
        headers = {
            'Referer' : 'http://www.cmbh.mg.gov.br/extras/verba_indenizatoria_nota_fiscal/oracle_lista_tipodespesa.php',
            'Origin' : 'http://www.cmbh.mg.gov.br',
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
            nature = base64.decodestring(nature).strip().decode('utf-8')
            date = parse_cmbh_date(base64.decodestring(month).strip().decode('utf-8'))

            session = Session()

            try:
                legislator = session.query(Legislator).filter(Legislator.name == legislator).one()
            except NoResultFound:
                legislator = Legislator(None, legislator, '', u'Vereador - Belo Horizonte')
                session.add(legislator)

            for row in data:
                columns = row.findAll('td')

                if not len(columns) == 5:
                    print u'Bad row: %s' % unicode(columns)
                    continue

                cnpj = columns[0].getText().replace('.','').replace('-', '').replace('/', '').strip()

                supplier_name = columns[1].getText().strip()

                try:
                    supplier_name = supplier_name.decode('utf-8')
                except Exception:
                    pass

                try:
                    supplier = session.query(Supplier).filter(Supplier.cnpj == cnpj).one()
                except NoResultFound:
                    supplier = Supplier(cnpj, supplier_name)
                    session.add(supplier)

                docnumber = columns[2].getText()
                expensed = parse_money(columns[3].getText())

                def print_expense(exp):
                    print u'%s (%d) expensed %f docnum: %s on %s supplier: %s (%s)' % \
                        (exp.legislator.name, exp.legislator.id, exp.expensed,
                         exp.number, exp.date, exp.supplier.name, exp.supplier.cnpj)

                try:
                    expense = session.query(Expense).filter(and_(Expense.number == docnumber,
                                                                 Expense.nature == nature,
                                                                 Expense.date == date,
                                                                 Expense.legislator == legislator,
                                                                 Expense.supplier == supplier)).one()
                    if self.debug:
                        print 'Found expense: ',
                        print_expense(expense)
                except NoResultFound:
                    expense = Expense(docnumber, nature, date, expensed,
                                      expensed, legislator, supplier)
                    session.add(expense)

                    if self.debug:
                        print 'NEW expense'
                        print_expense(expense)

            session.commit()

    def update_data(self, year = datetime.now().year):
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

def hack():
    return VerbaIndenizatoriaCMBH()

if __name__ == '__main__':
    v = hack()
    v.update_data()
