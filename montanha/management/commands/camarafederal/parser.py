# -*- coding: utf-8 -*-
#
# Copyright (©) 2013 Estêvão Samuel Procópio Amaral
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

import re
from datetime import datetime

max_legislators = 0


def parse_money(string):
    string = string.replace('R$ ', '')
    string = string.replace('.', '')
    string = string.replace(',', '.')
    return float(string)


def parse_date(string):
    return datetime.strptime(string, '%Y-%m-%d %H:%M:%S.%f').date()


class CamaraFederalParser:
    def parse_legislatures(self, content):
        select = content.find('select', {'name': 'Legislatura'})

        if not select:
            raise Exception("Invalid legislature content")

        legislatures = []

        options = select.findAll('option')[1:]
        for option in options:
            code = int(option['value'])
            #name = u'%d\u00AA Legislatura' % code
            info = unicode(option.text.strip())
            (junk, info) = info.split(' - ')
            (start, end) = info.split(' a ')

            start = '%s-01-01' % start
            end = '%s-12-31' % (int(end) - 1)

            legislatures.append({'original_id': code, 'date_start': start, 'date_end': end})

        return legislatures

    # FIXME: copied from senado's collector, should be shared!
    def _normalize_party_name(self, name):
        names_map = {
            'PCdoB': 'PC do B',
        }
        return names_map.get(name, name)

    def parse_legislators(self, content):
        table = content.find('table', {'class': 'cor', 'width': '100%'})

        if not table:
            raise Exception("Invalid legislators content")

        div = content.find('div', {'id': 'content'})
        summary = div.find('table')

        active = summary.findAll('b')[0].text.strip()
        total_active = [int(s) for s in active.split() if s.isdigit()][0]

        legislators = []

        tds = table.findAll('td')
        for td in tds:
            name = td.find('b').text.strip()
            original_id = int(td.find('a')['href'].split('=')[1])

            info = td.findAll('font', {'size': '1'})

            if len(info) == 1:
                break

            (party, state) = info[0].text.split(' - ')
            office = info[1].text.strip()
            phone = info[2].text.replace('Fone', '').strip()
            fax = info[3].text.replace('Fax', '').strip()
            email = info[4].text.strip()
            picture_uri = td.find('img')['src']

            legislators.append({'original_id': original_id, 'name': name.title(), 'party': self._normalize_party_name(party),
                                'state': state, 'office': office, 'phone': phone,
                                'fax': fax, 'email': email, 'picture_uri': picture_uri})

            if max_legislators > 0 and len(legislators) == max_legislators:
                break

        if len(legislators) != total_active:
            print '[Parser WARNING] parsed %d legislators from a list of %d.' % (len(legislators), total_active)

        return legislators

    def parse_total_expenses_per_nature(self, content):
        grid = content.find('div', {'class': 'grid'})
        if not grid:
            raise Exception("Invalid legislator expenses content")

        natures = []
        trs = grid.findAll('tr')[1:-1]
        for tr in trs:
            info = tr.find('a')
            total = tr.find('td', {'class': 'numerico'})
            querystring = info['href'].split('?')[1].split('&')
            for item in querystring:
                item = item.strip()
                (param, value) = item.split('=')

                if param == 'numSubCota':
                    original_id = int(value)
                    if original_id == 999:
                        name = unicode(info.text).replace('*', '').strip()
                    else:
                        name = unicode(info.text).strip()
                    total = parse_money(unicode(total.text).strip())
                    natures.append({'original_id': original_id, 'name': name, 'total': total})

        return natures

    def _parse_expenses_table(self, expenses_table, nature, year, month):
        expenses = []

        rows = expenses_table.findAll('tr')[1:-1]

        nature_total = 0
        for row in rows:
            columns = row.findAll('td')

            if len(columns) != 4 and len(columns) != 7:
                print u'Bad row (%s): %s' % (len(columns), unicode(columns))
                continue

            cnpj = unicode(columns[0].text.strip())
            supplier_name = unicode(columns[1].text.strip())
            docnumber = unicode(columns[2].text.strip())

            if len(columns) == 4:
                try:
                    value = expensed = parse_money(columns[3].text)
                except ValueError:
                    print 'Parser: NormalValueError for %s - %s (%s)' % (supplier_name,
                                                                         columns[3].text,
                                                                         docnumber)
                date = '%s-%s-01' % (year, month)
            elif len(columns) == 7:
                try:
                    value = expensed = parse_money(columns[6].text)
                except ValueError:
                    print 'Parser: FlightValueError for %s - %s (%s)' % (supplier_name,
                                                                         columns[6].text,
                                                                         docnumber)
                date = parse_date(columns[3].text)

            expenses.append({'cnpj': cnpj, 'supplier_name': supplier_name, 'docnumber': docnumber,
                             'value': value, 'expensed': expensed, 'date': date})
            nature_total += expensed

        if nature['total'] - nature_total > 0.01:
            print '[Parser WARNING] Nature total is %f, but expenses total is %f.' % (nature['total'], nature_total)

        return expenses

    def parse_nature_expenses(self, content, nature, year, month):
        grid = content.find('div', {'class': 'grid'})
        if not grid:
            raise Exception("Invalid legislator expenses content")

        expenses_table = grid.find('table', {'class': 'tabela-1', 'width': '100%'})
        expenses = self._parse_expenses_table(expenses_table, nature, year, month)

        return expenses

    def parse_legislator_expenses_per_nature(self, content, year, month):
        grid = content.find('div', {'class': 'grid'})
        if not grid:
            raise Exception("Invalid legislator expenses content")

        natures = grid.findAll('h4')
        expense_tables = grid.findAll('table')

        if len(natures) != len(expense_tables):
            raise Exception("Legislator expenses has incoherent information")

        expenses_per_nature = []

        for i in range(len(natures)):
            nature = unicode(re.sub('\s+', ' ', natures[i].text))

            rows = expense_tables[i].findAll('tr')[1:-1]

            expenses = []
            nature_total = 0
            for row in rows:
                columns = row.findAll('td')

                if len(columns) != 4 and len(columns) != 7:
                    print u'Bad row (%s): %s' % (len(columns), unicode(columns))
                    continue

                cnpj = unicode(columns[0].text.strip())
                supplier_name = unicode(columns[1].text.strip())
                docnumber = unicode(columns[2].text.strip())

                if len(columns) == 4:
                    try:
                        value = expensed = parse_money(columns[3].text)
                    except ValueError:
                        print 'Parser: NormalValueError for %s - %s (%s)' % (supplier_name,
                                                                             columns[3].text,
                                                                             docnumber)
                    date = '%s-%s-01' % (year, month)
                elif len(columns) == 7:
                    try:
                        value = expensed = parse_money(columns[6].text)
                    except ValueError:
                        print 'Parser: FlightValueError for %s - %s (%s)' % (supplier_name,
                                                                             columns[6].text,
                                                                             docnumber)
                    date = parse_date(columns[3].text)

                expenses.append({'cnpj': cnpj, 'supplier_name': supplier_name, 'docnumber': docnumber,
                                 'value': value, 'expensed': expensed, 'date': date})
                nature_total += expensed

            expenses_per_nature.append({'nature': nature, 'expenses': expenses, 'total': nature_total})

        return expenses_per_nature
