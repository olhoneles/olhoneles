# -*- coding: utf-8 -*-
from basesource import *
from cmbh.models import Legislator, Supplier, Expense
from cmbh import models

import base64


Session = models.initialize(get_database_path('cmbh'))


def parse_cmbh_date(date_string):
    month, year = date_string.split(' - ')

    day = '01'

    if month == u'Janeiro':
        month = '01'
    elif month == u'Fevereiro':
        month = '02'
    elif month == u'Março':
        month = '03'
    elif month == u'Abril':
        month = '04'
    elif month == u'Maio':
        month = '05'
    elif month == u'Junho':
        month = '06'
    elif month == u'Julho':
        month = '07'
    elif month == u'Agosto':
        month = '08'
    elif month == u'Setembro':
        month = '09'
    elif month == u'Outubro':
        month = '10'
    elif month == u'Novembro':
        month = '11'
    elif month == u'Dezembro':
        month = '12'
    else:
        raise Exception('Unknown month: ' + month)

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

    def retrieve_legislators(self, xls, month):
        uri  = 'http://www.cmbh.mg.gov.br/extras/verba_indenizatoria_nota_fiscal/lista_vereadores.php'
        data = { 'xls' : xls, 'mes' : month }
        headers = {
            'Referer' : 'http://www.cmbh.mg.gov.br/extras/verba_indenizatoria_nota_fiscal/lista_meses.php',
            'Origin' : 'http://www.cmbh.mg.gov.br',
            }
        return BaseCollector.retrieve_uri(self, uri, data, headers)

    def retrieve_expense_types(self, xls, month, legislator, line):
        uri  = 'http://www.cmbh.mg.gov.br/extras/verba_indenizatoria_nota_fiscal/lista_tipodespesa.php'
        data = { 'xls' : xls, 'mes' : month, 'vereador': legislator, 'linha' : line }
        headers = {
            'Referer' : 'http://www.cmbh.mg.gov.br/extras/verba_indenizatoria_nota_fiscal/lista_vereadores.php',
            'Origin' : 'http://www.cmbh.mg.gov.br',
            }
        return BaseCollector.retrieve_uri(self, uri, data, headers)

    def retrieve_actual_data(self, xls, line, column, legislator, nature, month):
        uri  = 'http://www.cmbh.mg.gov.br/extras/verba_indenizatoria_nota_fiscal/lista_valordespesa.php'
        data = {
            'xls' : xls,
            'linha' : line,
            'coluna' : column,
            'vereador': legislator,
            'tipodespesa' : nature,
            'mes' : month
            }
        headers = {
            'Referer' : 'http://www.cmbh.mg.gov.br/extras/verba_indenizatoria_nota_fiscal/lista_tipodespesa.php',
            'Origin' : 'http://www.cmbh.mg.gov.br',
            }
        return BaseCollector.retrieve_uri(self, uri, data, headers)

    def update_legislators(self):
        pass

    def update_data_for_legislator(self, xls, month, legislator, line):
        expense_types = self.retrieve_expense_types(xls, month, legislator, line)

        if not expense_types:
            return

        # Ignore the last one, which is the total.
        expense_types = expense_types.find('ul').findAll('a')[:-1]

        parameters_list = []
        for etype in expense_types:
            parts = etype['onclick'].split("'")
            xls = parts[1]
            line = parts[3]
            column = parts[5]
            legislator = parts[7]
            nature = parts[9]
            month = parts[11]

            data = self.retrieve_actual_data(xls, line, column, legislator, nature, month)

            if not data:
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

                if not len(columns) == 4:
                    try:
                        print u'Bad row: %s' % columns.decode('utf-8')
                    except UnicodeEncodeError:
                        print u'Bad row: %s' % unicode(columns)
                    continue

                if not len(columns) == 4:
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

        parameters_list = []
        for month in months:
            anchor = month.find('a')
            parts = anchor['onclick'].split("'")
            parameters_list.append((parts[1], parts[3]))

        for parameters in parameters_list:
            print base64.decodestring(parameters[0]), base64.decodestring(parameters[1])
            leg_list = self.retrieve_legislators(*parameters)
            anchors = leg_list.find('ul').findAll('a')
            for anchor in anchors:
                parts = anchor['onclick'].split("'")
                xls = parts[1]
                line = parts[3]
                legislator = parts[5]
                month = parts[7]
                self.update_data_for_legislator(xls, month, legislator, line)

def hack():
    return VerbaIndenizatoriaCMBH()

if __name__ == '__main__':
    v = hack()
    v.update_data()
