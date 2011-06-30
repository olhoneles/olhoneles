from base import *

class VerbaIndenizatoriaALMG(BaseCollector):

    legislatures = [17]
    main_uri = 'http://www.almg.gov.br/index.asp?diretorio=verbasindeniz&arquivo=ListaMesesVerbas%(legislature)d'
    sub_uri = 'http://www.almg.gov.br/VerbasIndeniz/%(year)s/%(legid)d/%(month).2ddet.asp'

    def update_legislators_for_legislature(self, legislature):
        # Retrieving the first select from current legislature
        select = self.get_element_from_uri(self.main_uri % dict(legislature=legislature), 'select')

        # We ignore the first one because it is a placeholder.
        options = select.findAll('option')[1:]

        # Turn the soup objects into a list of dictionaries
        legislators = []
        for item in options:
            legislators.append(dict(id = int(item['matr']),
                                    name = item['name'],
                                    party = item.string[len(item['name'])+2:-1],
                                    )
                               )

        # Obtain the existing ids
        session = Session()
        existing_ids = [item[0] for item in session.query(Legislator.id)]

        # Add legislators that do not exist yet
        for l in legislators:
            if l['id'] not in existing_ids:
                session.add(Legislator(l['id'], l['name'], l['party'], u'Deputado Estadual - MG'))

        session.commit()

    def update_legislators(self):
        if self.debug:
            print 'Retrieving legislators information...'
        for legislature in self.legislatures:
            self.update_legislators_for_legislature(legislature)

    def update_data(self, year = datetime.now().year):
        session = Session()
        ids = [item[0] for item in session.query(Legislator.id)]

        for legislator_id in ids:
            for month in range(1, 13):
                if self.debug:
                    print 'Retrieving info for legid %s, month %s' % (legislator_id, month)
                self.update_data_for_id(legislator_id, year, month)

    def update_data_for_id(self, id, year, month):
        session = Session()

        legislator = session.query(Legislator).get(id)

        content = self.retrieve_uri(self.sub_uri % dict(year = year, legid = id, month = month))
        if content == None:
            return

        # Find the main content table. It looks like this:
        #
        # <table>
        #   <tr><td><strong>Description here</strong></td></tr>
        #   <tr><table>[Table with the actual data comes here]</table></tr>
        #   <tr><td><strong>Another description here</strong></td></tr>
        #   ... and so on.
        content = content.findAll('table')[2].findChild('tr')

        # Obtain all of the top-level rows.
        expenses_tables = [content] + content.findNextSiblings('tr')

        # Match the description to the tables (even rows are
        # descriptions, odd rows are data tables).
        expenses = []
        for x in range(0, len(expenses_tables), 2):
            expenses.append((expenses_tables[x],
                             expenses_tables[x+1]))

        # Parse the data.
        for desc, exp in expenses:
            nature = desc.find('strong').contents[0]

            exp = exp.find('table').findChild('tr').nextSibling.findNextSiblings('tr')
            for row in exp:
                columns = row.findAll('td')

                try:
                    name = columns[0].find('div').contents[0]
                    cnpj = str(columns[1].find('div').contents[0])
                except IndexError:
                    continue

                try:
                    supplier = session.query(Supplier).filter(Supplier.cnpj == cnpj).one()
                except NoResultFound:
                    supplier = Supplier(cnpj, name)
                    session.add(supplier)

                try:
                    docnumber = columns[2].find('div').contents[0]
                    docdate = parse_date(columns[3].find('div').contents[0])
                    docvalue = parse_money(columns[4].find('div').contents[0])
                    expensed = parse_money(columns[5].find('div').contents[0])
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
