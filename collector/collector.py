#!/usr/bin/python

from logging import exception
from urllib2 import urlopen, URLError

from BeautifulSoup import BeautifulSoup

from models import Session, Legislator

class VerbaIndenizatoria(object):

    main_uri = 'http://almg.gov.br/index.asp?diretorio=verbasindeniz&arquivo=ListaMesesVerbas'
    sub_uri = 'http://almg.gov.br/VerbasIndeniz/%(year)s/%(legid)d/%(month).2ddet.asp'

    def update_legislators(self):
        try:
            url = urlopen(self.main_uri)
        except URLError:
            exception('Unable to download "%s": ')

        content = BeautifulSoup(url.read())

        # We ignore the first one because it is a placeholder.
        options = content.find('select').findAll('option')[1:]

        # Turn the soup objects into a list of dictionaries
        legislators = []
        for item in options:
            legislators.append(dict(id = int(item['matr']),
                                    name = item['name'],
                                    )
                               )

        # Obtain the existing ids
        session = Session()
        existing_ids = [item[0] for item in session.query(Legislator.id)]

        # Add legislators that do not exist yet
        for l in legislators:
            if l['id'] not in existing_ids:
                session.add(Legislator(l['id'], l['name']))

        session.commit()

    def update_data_for_id(self, id):
        try:
            url = urlopen(self.sub_uri % dict(year = 2010, legid = id, month = 1))
        except URLError:
            exception('Unable to download "%s": ')

        content = BeautifulSoup(url.read())

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
            try:
                description = desc.find('strong').contents[0]
                print description

                exp = exp.find('table').findChild('tr').nextSibling.findNextSiblings('tr')
                for row in exp:
                    columns = row.findAll('td')
                    supplier = columns[0].find('div').contents[0]
                    print supplier

            except AttributeError:
                pass

if __name__ == '__main__':
    vi = VerbaIndenizatoria()
    vi.update_legislators()
    vi.update_data_for_id(12193)
