# coding=utf-8
from base import *
from sqlalchemy import distinct

import re

class VerbaIndenizatoriaCamara(BaseCollector):

    legislators_uri = 'http://www2.camara.gov.br/transparencia/cota-para-exercicio-da-atividade-parlamentar/verba_indenizatoria_index'
    expenses_uri = 'http://www2.camara.gov.br/transparencia/cota-para-exercicio-da-atividade-parlamentar/verba_indenizatoria_detalheVerbaAnalitico?nuDeputadoId=%s&numMes=%s&numAno=%s'

    position = u'Deputado Federal'

    def update_legislators(self):
        if self.debug:
            print 'Retrieving legislators...'

        # Retrieving the select with legislators information
        select = self.get_element_from_uri (self.legislators_uri, 'select', {'id' : 'listaDep'})

        # We ignore the first one because it's a placeholder.
        options = select.findAll('option')[1:]

        # Turn the soup objects into a list of dictionaries
        legislators = []
        for item in options:
            item = item['value']

            # Parsing the value string
            #   <option value="[name]|[party]|[state]|[id]|[start_of_legislature]">[name with legislature information]</option>
            name, party, garbage, cod, garbage = item.split('|')

            legislators.append(dict(id=int(cod), name=name.strip(), party=party.strip()))

        # Obtain the existing ids
        session = Session()
        existing_ids = [item[0] for item in session.query(Legislator.id).filter(Legislator.position == self.position)]

        # Add legislators that do not exist yet
        for l in legislators:
            if l['id'] not in existing_ids:
               session.add(Legislator(l['id'], l['name'], l['party'], self.position))

        session.commit()

    def update_data(self, year = datetime.now().year):
        self.update_data_normal (year, 1712)
        #self.update_data_missing (year, 81)
        #self.update_data_manual (81, year)

    def update_data_missing(self, year = datetime.now().year, start = None):
        session = Session()

        existing_ids = session.query(distinct(Expense.legislator_id)).filter(and_(Expense.date >= '%s-01-01'%(year),
                                                                                  Expense.date <= '%s-12-31'%(year)));
        if start == None:
            legislators = session.query(Legislator.id).filter(Legislator.id.op('NOT IN')(existing_ids)).all()
        else:
            legislators = session.query(Legislator.id).filter(and_(Legislator.id.op('NOT IN')(existing_ids),
                                                                   Legislator.id >= start)).all()
        for l in legislators:
            for m in range(1, 13):
                self.update_data_for_id_period (l.id, year, m)

    def update_data_manual(self, id, year = datetime.now().year):
        session = Session()

        for month in range(1, 13):
            self.update_data_for_id_period(id, year, month)


    def update_data_normal(self, year = datetime.now().year, start = None):
        session = Session()
        if start == None:
            data = [item for item in session.query(Legislator.id, Legislator.name).filter(Legislator.position == self.position)]
        else:
            data = [item for item in session.query(Legislator.id, Legislator.name).filter(and_(Legislator.position == self.position,
                                                                                               Legislator.id >= start))]

        date = datetime.now()
        for legislator_id, name in data:
            try:
                if year == date.year:
                    for month in range(date.month-2, date.month+1):
                        self.update_data_for_id_period(legislator_id, year, month)
                else:
                    for month in range(1, 13):
                        self.update_data_for_id_period(legislator_id, year, month)
            except HTTPError as msg:
                print "Error retrieving expenses: %s\n" % (msg)
                continue

        return


    def update_data_for_id_period(self, id, year, month):
        session = Session()

        # Retrieving legislator
        legislator = session.query(Legislator).filter(Legislator.id == id).one()

        # Find the main content div. It looks like this:
        #
        # <div class="grid">
        #   <div class="grid-cell ...">
        #     <h4 class="header ...">[Category]</h4>
        #     <table class="tabela-1">[Table with expenses per supplier]</table>
        #   </div>
        #   ... and so on.
        # </div>

        if self.debug:
            print "Retrieving expenses for %s (%d) in %s/%s" % (legislator.name, legislator.id, month, year)
        try:
            div = self.get_element_from_uri (self.expenses_uri %(id, month, year),
                                             'div', {'class' : 'grid'});
        except HTTPError, e:
            # Error 500 indicates that there's no expense information available
            if e.getcode() == 500:
                return

        # Obtain expenses information. Another div holds an 
        # h4 (the category) and the expense table.
        #
        # The expense table looks like this:
        #
        # <table>
        #   <tr><td>[cnpj]</td><td title="[supplier]">[abbr. supplier]</td><td>[docnumber]</td><td>[value]</td></tr>
        #   ... and so on.
        # </table>
        for expenses in div.findAll('div'):
            nature = BeautifulStoneSoup(expenses.find('h4').text, convertEntities=BeautifulStoneSoup.HTML_ENTITIES).text
            for row in expenses.findAll('tr')[1:]:
                columns = row.findAll('td')

                try:
                    name = BeautifulStoneSoup(columns[1].text, convertEntities=BeautifulStoneSoup.HTML_ENTITIES).text
                    cnpj = columns[0].text
                except IndexError:
                    continue

                try:
                    supplier = session.query(Supplier).filter(Supplier.cnpj == cnpj).one()
                except NoResultFound:
                    supplier = Supplier(cnpj, name)
                    session.add(supplier)

                try:
                    docnumber = columns[2].text

                    if len(columns) == 4:
                        docvalue = parse_money(columns[3].text)
                        docdate = parse_date('01/%s/%s' %(month, year))
                    if len(columns) == 7:
                        docvalue = parse_money(columns[6].text)
                        docdate = parse_date(columns[3].text)
                        
                    expensed = docvalue
                except IndexError:
                    continue

                if self.debug:
                    print "Expensed %s with %s (doc %s) on %s" %(expensed, nature, docnumber, docdate)
                try:
                    expense = session.query(Expense).filter(and_(Expense.number == docnumber,
                                                                 Expense.nature == nature,
                                                                 Expense.date == docdate,
                                                                 Expense.legislator == legislator,
                                                                 Expense.supplier == supplier,
                                                                 Expense.expensed == expensed)).one()
                except NoResultFound:
                    expense = Expense(docnumber, nature, docdate, docvalue,
                                      expensed, legislator, supplier)
                    session.add(expense)

        session.commit()
                
    def update_data_for_id_nudeputado_period(self, id, nuDeputado, year, month):
        session = Session()

        # Retrieving legislator
        legislator = session.query(Legislator).filter(Legislator.id == id).one()

        # Find the main content div. It looks like this:
        #
        # <div class="grid">
        #   <div class="grid-cell ...">
        #     <h4 class="header ...">[Category]</h4>
        #     <table class="tabela-1">[Table with expenses per supplier]</table>
        #   </div>
        #   ... and so on.
        # </div>

        try:
            div = self.get_element_from_uri (self.expenses_uri %(nuDeputado, month, year),
                                             'div', {'class' : 'grid'});
        except HTTPError, e:
            # Error 500 indicates that there's no expense information available
            if e.getcode() == 500:
                return

        # Obtain expenses information. Another div holds an 
        # h4 (the category) and the expense table.
        #
        # The expense table looks like this:
        #
        # <table>
        #   <tr><td>[cnpj]</td><td title="[supplier]">[abbr. supplier]</td><td>[docnumber]</td><td>[value]</td></tr>
        #   ... and so on.
        # </table>
        for expenses in div.findAll('div'):
            nature = BeautifulStoneSoup(expenses.find('h4').text, convertEntities=BeautifulStoneSoup.HTML_ENTITIES).text
            for row in expenses.findAll('tr')[1:]:
                columns = row.findAll('td')

                try:
                    name = BeautifulStoneSoup(columns[1].text, convertEntities=BeautifulStoneSoup.HTML_ENTITIES).text
                    cnpj = columns[0].text
                except IndexError:
                    continue

                try:
                    supplier = session.query(Supplier).filter(Supplier.cnpj == cnpj).one()
                except NoResultFound:
                    supplier = Supplier(cnpj, name)
                    session.add(supplier)

                try:
                    docnumber = columns[2].text

                    if len(columns) == 4:
                        docvalue = parse_money(columns[3].text)
                        docdate = parse_date('01/%s/%s' %(month, year))
                    if len(columns) == 7:
                        docvalue = parse_money(columns[6].text)
                        docdate = parse_date(columns[3].text)
                        
                    expensed = docvalue
                except IndexError:
                    continue

                try:
                    expense = session.query(Expense).filter(and_(Expense.number == docnumber,
                                                                 Expense.nature == nature,
                                                                 Expense.date == docdate,
                                                                 Expense.legislator == legislator,
                                                                 Expense.supplier == supplier)).one()
                except NoResultFound:
                    expense = Expense(docnumber, nature, docdate, docvalue,
                                      expensed, legislator, supplier)
                    session.add(expense)

        session.commit()
