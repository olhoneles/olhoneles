# coding=utf-8
from basesource import *
from base.models import models
from base.models.models import Legislator, Supplier, Expense


Session = models.initialize(get_database_path('senado'))


class VerbaIndenizatoriaSenado(BaseCollector):

    legislators_uri = 'http://www.senado.gov.br/senadores/default.asp'
    vi_uri = 'http://www.senado.gov.br/transparencia/verba/asp/verbaAnoSenador.asp?CodParl=%(legislator)d'
    vi_info_uri = 'http://www.senado.gov.br/transparencia/verba/asp/Verba%s.asp'

    NOME = 0
    PARTIDO = 1

    position = u'Senador'

    def __retrieve_legislator_info(self, tr):
        tds = tr.findAll('td')
        return dict(id = int(filter(lambda x: x.isdigit(), tds[self.NOME].a['href'])),
             name = BeautifulStoneSoup(tds[self.NOME].text, convertEntities=BeautifulStoneSoup.HTML_ENTITIES).text,
             party = tds[self.PARTIDO].text,
             position = self.position,
             )

    def update_legislators(self):
        # Retrieving the table with legislators information
        table = self.get_element_from_uri (self.legislators_uri, 'table', {'id' : 'senadores'})

        # We ignore the first one because it is a placeholder.
        options = table.findAll('tr')[1:]

        # Turn the soup objects into a list of dictionaries
        legislators = []
        for item in options:
            item = self.__retrieve_legislator_info (item)
            legislators.append(item)

        # Obtain the existing ids
        session = Session()
        existing_ids = [item[0] for item in session.query(Legislator.id).filter(Legislator.position == self.position)]

        # Add legislators that do not exist yet
        for l in legislators:
            if l['id'] not in existing_ids:
                session.add(Legislator(l['id'], l['name'], l['party'], self.position))

        session.commit()

    def __retrieve_cod_orgao(self, legislator):
        ipt = self.get_element_from_uri(self.vi_uri % dict(legislator=legislator),
                                                  'input', {'name' : 'COD_ORGAO'})
        return ipt['value']


    def update_data(self, year = datetime.now().year):
        session = Session()
        ids = [item[0] for item in session.query(Legislator.id).filter(Legislator.position == self.position)]

        for legislator_id in ids:
            self.update_data_for_id(legislator_id, year)

    # move to base.py
    def get_month_by_name (self, month):
        months = [u'JANEIRO', u'FEVEREIRO', u'MARÇO', u'ABRIL', u'MAIO', u'JUNHO', u'JULHO', u'AGOSTO', u'SETEMBRO', u'OUTUBRO', u'NOVEMBRO', u'DEZEMBRO']
        m = months.index(month) + 1
        return m
                
    def update_data_for_id(self, id, year):
        vi_info = dict(COD_ORGAO = self.__retrieve_cod_orgao (id), ANO_EXERCICIO = year)
        frmPeriodo = self.get_element_from_uri(self.vi_info_uri % ('MesSenador'), 'form', {'id' : 'frmPeriodo'}, vi_info)
        if frmPeriodo == None:
            if self.debug:
                print vi_info, 'nenhum dado lançado'
            return

        vi_info = dict(ANO_EXERCICIO = year, LEGISLATOR = id)
        for ipt in frmPeriodo.findAll('input'):
            vi_info[ipt['name']] = ipt['value'].encode('iso-8859-1')

        for period in frmPeriodo.find('select', {'name' : 'COD_PERIODO'}).findAll('option')[1:]:
            vi_info['COD_PERIODO'] = period['value']
            self.update_data_for_id_period(vi_info)

    def update_data_for_id_period(self, data):
        session = Session()

        # Retrieving legislator
        legislator = session.query(Legislator).filter(Legislator.id == data['LEGISLATOR']).one()

        # Find the main content table. It looks like this:
        #
        # <table>
        #   <tr><td><dl><dt>[Category]</dt><dd><table>[Table with expenses per supplier]</table></dd></dl></td><td>[Total of category]</td></tr>
        #   ... and so on.
        # </table>
        if self.debug:
            print "Retrieving info for %s" % (data)
        table = self.get_element_from_uri(self.vi_info_uri % ('Mes'), 'table', {}, data)

        # Obtain the expenses information. It's dl where the
        # dt is the category and the dd is the expense table.
        #
        # The expense table looks like this:
        #
        # <table>
        #   <tr><td>[cnpj]</td><td title="[supplier]">[abbr. supplier]</td><td>[docnumber]</td><td>[value]</td></tr>
        #   ... and so on.
        # </table>
        for expenses in table.findAll('dl'):
            nature = expenses.find('dt').text
            for row in expenses.findAll('tr')[1:]:
                columns = row.findAll('td')

                try:
                    name = columns[1]['title']
                    cnpj = columns[0].text
                except IndexError:
                    continue

                try:
                    supplier = session.query(Supplier).filter(Supplier.cnpj == cnpj).one()
                except NoResultFound:
                    print 'added'
                    supplier = Supplier(cnpj, name)
                    session.add(supplier)

                try:
                    docnumber = columns[2].text
                    docdate = parse_date(columns[3].text)

                    if len(columns) == 5:
                        docvalue = parse_money(columns[4].text)
                    if len(columns) == 6:
                        docvalue = parse_money(columns[5].text)

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
                print nature, docnumber, docdate, docvalue, expensed

        session.commit()
