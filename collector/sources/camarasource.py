# coding=utf-8
from basesource import *
from base.models import models
from base.models.models import Legislator, Supplier, Expense
from sqlalchemy import distinct

Session = models.initialize(get_database_path('camara'))

class VerbaIndenizatoriaCamara(BaseCollector):
    position = u'Deputado Federal'

    def retrieve_legislators(self):
        if self.debug:
            print 'Retrieving legislators...'

        uri  = 'http://www2.camara.gov.br/transparencia/cota-para-exercicio-da-atividade-parlamentar'
        headers = {
            'Referer' : 'http://www2.camara.gov.br/transparencia',
            'Origin' : 'http://www2.camara.gov.br',
            }
        return BaseCollector.retrieve_uri(self, uri=uri, headers=headers)

    def retrieve_month_expenses(self, legid, year, month):
        session = Session()
        legislator = session.query(Legislator.id, Legislator.name).filter(Legislator.id == legid).one()
        if self.debug:
            print "Retrieving expenses for %s (%d) in %s-%s" % (legislator.name, legislator.id, year, month)

        uri  = 'http://www2.camara.gov.br/transparencia/cota-para-exercicio-da-atividade-parlamentar/verba_indenizatoria_detalheVerbaAnalitico?nuDeputadoId=%s&numMes=%s&numAno=%s&numSubCota='
        headers = {
            'Referer' : 'http://www2.camara.gov.br/transparencia/cota-para-exercicio-da-atividade-parlamentar/verba_indenizatoria_retPesquisaDep',
            'Origin' : 'http://www2.camara.gov.br',
            }
        return BaseCollector.retrieve_uri(self, uri=uri % (legid, month, year), headers=headers)

    def update_legislators(self):
        # Retrieving html and select with legislators information
        html = self.retrieve_legislators()
        select = html.find('select', {'id' : 'listaDep'})

        # We ignore the first option because it's a placeholder.
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
        session = Session()
        legislators = [item for item in session.query(Legislator.id).filter(Legislator.position == self.position)]

        date = datetime.now()
        for legislator in legislators:
            try:
                if year == date.year:
                    for month in range(date.month-2, date.month+1):
                        self.update_data_for_id_period(legislator.id, year, month)
                else:
                    for month in range(1, 13):
                        self.update_data_for_id_period(legislator.id, year, month)
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
        html = self.retrieve_month_expenses(id, year, month)
        div = html.find('div', {'class' : 'grid'})

        if div is None:
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
