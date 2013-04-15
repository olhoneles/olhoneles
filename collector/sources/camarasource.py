# coding=utf-8
import urlparse

from basesource import *
from base.models import models
from base.models.models import Legislator, Supplier, Expense
from sqlalchemy import distinct

from utils.cache import timedelta, RequestCache

Session = models.initialize(get_database_path('camara'))

class VerbaIndenizatoriaCamara(BaseCollector):
    cache = RequestCache ('/tmp/montanha/camara');
    cache_default_expiry = timedelta (days=15)
    position = u'Deputado Federal'

    def retrieve_uri(self, uri, data = {}, headers = {}, cache_file = None, cache_expiry = None):
        # if no cache_file informed, keep the current behaviour
        if cache_file == None:
            return BaseCollector.retrieve_uri (self, uri, data, headers)

        if cache_expiry == None:
            cache_expiry = self.cache_default_expiry

        if not self.cache.exists (cache_file) or self.cache.expired (cache_file, cache_expiry):
            content = BaseCollector.retrieve_uri (self, uri, data, headers)
            # do not write to disk if there's nothing to write
            if content is None:
                return content
            self.cache.write (cache_file, str(content))

        return BeautifulSoup (self.cache.read (cache_file))        

    def retrieve_legislators(self):
        cache_file = 'legislators'
        uri  = 'http://www2.camara.leg.br/transparencia/cota-para-exercicio-da-atividade-parlamentar'
        headers = {
            'Referer' : 'http://www2.camara.leg.br/transparencia',
            'Origin' : 'http://www2.camara.leg.br',
            }
        html = self.retrieve_uri(uri, headers=headers, cache_file=cache_file)

        # Find the legislators' select. It looks like this:
        #
        # <select name="listaDep" id="listaDep">
        #   <option ...>
        #   ... and so on.
        # </select>
        select = html.find('select', {'id' : 'listaDep'})

        # We ignore the first option because it's a placeholder.
        options = select.findAll('option')[1:]
        return options

    def __legislator_parse_data__ (self, legislator):
        data = legislator['value']

        # Parsing the value string
        #   <option value="[name]|[party]|[state]|[id]|[start_of_legislature]">[name with legislature information]</option>
        name, party, state, cod, leg_start = data.split('|')

        return dict(id=int(cod), name=name.strip(), party=party.strip(), state=state, leg_start=int(leg_start))

    def retrieve_month_totals(self, legid, year, month):
        # Retrieving legislator from html to recover state, which is not saved to the database
        leg = [l for l in self.retrieve_legislators () if '|%s|' % legid in l['value']][0]
        legislator = self.__legislator_parse_data__ (leg)

        if self.debug:
            print "Retrieving totals for %s (%d) in %s-%s" % (legislator['name'], legislator['id'], year, month)

        legname = legislator['name'].lower ().replace (' ', '_')
        cache_file = 'expenses-summary-%s-%s-%s' % (year, month, legname)
        uri  = 'http://www2.camara.leg.br/transparencia/cota-para-exercicio-da-atividade-parlamentar/verba_indenizatoria_retPesquisaDep'
        data = {
            'mesAno' : '%s/%s' % (month, year),
            'listaDep' : ('%s|%s|%s' % (legislator['name'], legislator['party'], legislator['state'])).encode ('latin-1')
            }
        headers = {
            'Referer' : 'http://www2.camara.leg.br/transparencia/cota-para-exercicio-da-atividade-parlamentar/verba_indenizatoria_retPesquisaDep',
            'Origin' : 'http://www2.camara.leg.br',
            }
        
        html = self.retrieve_uri(uri, data, headers, cache_file)

        # Find the expense totals table. It looks like this:
        #
        # <table class="tabela-1" width="100%" border="0" summary="Lista das despesas com CEAP">
        #   <tr>
        #     <th scope="col">Classifica&ccedil;&atilde;o da despesa</th>
        #     <th class="numerico" scope="col">Valor</th>
        #   </tr>
        #   ... and so on.
        # </table>
        # So we leave the first and last trs because they're only header and footer
        table = html.find('table', {'class' : 'tabela-1'})
        if table:
            return table.findAll ('tr')[1:-1]

        return []

    def month_total_parse_data (self, month_expenses):
        data = month_expenses.findAll ('td')
        expense_info = data[0].find ('a')
        expense_info = urlparse.parse_qs (expense_info['href'].split('?')[1])
        return dict (
            legid = int (expense_info['nuDeputadoId'][0]),
            month = int (expense_info['numMes'][0]),
            year = int (expense_info['numAno'][0]),
            category_id = int (expense_info['numSubCota'][0]),
            description = BeautifulStoneSoup (data[0].text, convertEntities=BeautifulStoneSoup.HTML_ENTITIES).text,
            total = parse_money (data[1].text)
            )

    def retrieve_category_expenses (self, legid, year, month, category):
        # Retrieving legislator from database
        session = Session()
        legislator = session.query(Legislator).filter(Legislator.id == legid).one()

        if self.debug:
            print "Retrieving expenses in category %s by %s (%d) in %s-%s" % (category, legislator.name, legislator.id, year, month)

        legname = legislator.name.lower ().replace (' ', '_')
        cache_file = 'category-expenses-%s-%s-%s-%s' % (year, month, legname, category)
        uri  = 'http://www2.camara.leg.br/transparencia/cota-para-exercicio-da-atividade-parlamentar/verba_indenizatoria_detalheVerbaAnalitico?nuDeputadoId=%s&numMes=%s&numAno=%s&numSubCota=%s'
        headers = {
            'Referer' : 'http://www2.camara.leg.br/transparencia/cota-para-exercicio-da-atividade-parlamentar/verba_indenizatoria_retPesquisaDep',
            'Origin' : 'http://www2.camara.leg.br',
            }
        
        html = self.retrieve_uri(uri % (legid, month, year, category), headers=headers, cache_file=cache_file)

        # Find the expenses. It looks like this:
        #
        # <div class="grid">
        #   <div ...>
        #     <h4 ...>[category]</h4>
        #     <table class="tabela-1" ...>
        #        <tr ...>
        #          <th>CNPJ/CPF</th>
        #          <th>Nome do Fornecedor</th>
        #          <th>NF/Recibo</th>
        #          <th>Valor Reembolsado</th>
        #        </tr>
        #        ... and so on.
        #      </table>
        #   </div>
        # </div>
        return html.find ('div', {'class' : 'grid'})

    def update_legislators(self):
        # Retrieving html and select with legislators information
        options = self.retrieve_legislators()

        # Turn the soup objects into a list of dictionaries
        legislators = []
        for item in options:
            legislators.append (self.__legislator_parse_data__ (item))

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
                        self.update_data_for_legislator(legislator.id, year, month)
                else:
                    for month in range(1, 13):
                        self.update_data_for_legislator(legislator.id, year, month)
            except HTTPError as msg:
                print "Error retrieving expenses: %s\n" % (msg)
                continue

        return

    def update_data_for_legislator(self, legid, year, month):
        # Retrieving legislator from database
        session = Session()
        legislator = session.query(Legislator).filter(Legislator.id == legid).one()

        # For each category of expenses, we need to fetch the detailed expense list
        totals = self.retrieve_month_totals(legid, year, month)
        for total in totals:
            total = self.month_total_parse_data (total)
            div = self.retrieve_category_expenses (legid, year, month, total['category_id'])

            if div is None:
                continue # next category

            # Obtain expenses information. Another div holds an 
            # h4 (the category) and the expense table.
            #
            # The expense table looks like this:
            #
            # <table>
            #   <tr><td>[cnpj]</td><td title="[supplier]">[abbr. supplier]</td><td>[docnumber]</td><td>[value]</td></tr>
            #   ... and so on.
            # </table>
            nature = BeautifulStoneSoup(div.find('h4').text, convertEntities=BeautifulStoneSoup.HTML_ENTITIES).text
            for row in div.findAll('tr')[1:]:
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
