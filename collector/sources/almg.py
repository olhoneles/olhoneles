from base import *

class VerbaIndenizatoriaALMG(BaseCollector):

    main_uri = 'http://www.almg.gov.br/acompanhe/prestacao_contas/index.html?pager.offset=%(offset)d&aba=js_tabVerba'
    sub_uri = 'http://www.almg.gov.br/deputados/verbas_indenizatorias/index.html?idDep=%(legid)d'

    def update_legislators(self):
        if self.debug:
            print 'Retrieving legislators information...'

        # Get a list of all available legislators.
        legislators = []
        for offset in range(0, 73, 12):
            ul = self.get_element_from_uri(self.main_uri % dict(offset = offset), 'ul', dict(id = 'deputados_view-imagem'))

            list_items = ul.findAll('li')

            # Each item looks like this:
            # <p class="titulo">
            #   <a href="/deputados/verbas_indenizatorias/index.html?idDep=[ID]">[NAME]</a>
            # </p>
            # <p>Partido: [PARTY]</p>
            for item in list_items:
                paras = item.findAll('p')

                link = paras[0].findChild('a')

                legid = link['href'].split('idDep=')[1]
                name = link.getText()

                party = paras[1].getText().split(' ')[1]

                legislators.append(dict(id = int(legid),
                                        name = name,
                                        party = party,
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

    def update_data(self, year = datetime.now().year):
        session = Session()
        ids = [item[0] for item in session.query(Legislator.id)]

        for legislator_id in ids:
            for month in range(1, 13):
                if self.debug:
                    print 'Retrieving info for legid %d, month %d, year %d' % (legislator_id, month, year)
                self.update_data_for_id(legislator_id, year, month)

    def update_data_for_id(self, legid, year, month):
        session = Session()

        legislator = session.query(Legislator).get(legid)

        content = self.retrieve_uri(self.sub_uri % dict(legid = legid),
                                    dict(year = year, month = month))
        if content == None:
            return

        # Find the main content table. It looks like this:
        #
        # <ul class="listaFAQ" id="box-toggle">
        #   <li class="primeira cor">
        #     <span class="js_toggleNext"...>
        #       <span class="verbas-item1">
        #          <strong>[Nature of expense]</strong>
        #       </span>
        #       <span class="valores-verba">[Total for expenses of this nature]</span>
        #       <div ...></div> (yes, empty)
        #     </span>
        #     <span class="clear" style="display: inline;">
        #       [Actual data comes here]
        #     </span>
        #   </li>
        # ... and so on.
        content = content.findChild('ul', { 'class' : 'listaFAQ', 'id' : "box-toggle" })

        if content == None:
            if self.debug:
                print 'No expenses found for legislator %d on month %d of year %d' % (legid, month, year)
            return

        tables = content.findAll('li')
        for table in tables:
            nature = table.findChild('strong').getText()

            for row in table.findAll('tr'):
                columns = row.findAll('td')

                name = columns[0].getText()
                cnpj = columns[1].getText()

                try:
                    supplier = session.query(Supplier).filter(Supplier.cnpj == cnpj).one()
                except NoResultFound:
                    supplier = Supplier(cnpj, name)
                    session.add(supplier)

                docdate = parse_date(columns[2].getText())
                docnumber = columns[3].getText()

                docvalue = parse_money(columns[4].getText())
                expensed = parse_money(columns[5].getText())

                def print_expense(exp):
                    try:
                        print u'%s (%d) expensed %f docnum: %s on %s supplier: %s (%s)' % \
                            (exp.legislator.name, exp.legislator.id, exp.expensed,
                             exp.number, exp.date, exp.supplier.name, exp.supplier.cnpj)
                    except Exception:
                        import pdb;pdb.set_trace()

                try:
                    expense = session.query(Expense).filter(and_(Expense.number == docnumber,
                                                                 Expense.nature == nature,
                                                                 Expense.date == docdate,
                                                                 Expense.legislator == legislator,
                                                                 Expense.supplier == supplier)).one()
                    if self.debug:
                        print 'Found expense: ',
                        print_expense(expense)
                except NoResultFound:
                    expense = Expense(docnumber, nature, docdate, docvalue,
                                      expensed, legislator, supplier)
                    session.add(expense)

                    if self.debug:
                        print 'NEW expense'
                        print_expense(expense)

            session.commit()
