# -*- coding: utf-8 -*-
#
# Copyright (c) 2018, Marcelo Jorge Vieira
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

from datetime import datetime

from slugify import slugify

from basecollector import BaseCollector
from montanha.models import (
    ArchivedExpense, ExpenseNature, Institution, Legislature, Legislator,
    PoliticalParty, Supplier
)


ALEPE_URL = 'http://www.alepe.pe.gov.br'
TRANSPARENCIA_URL = '{0}/transparencia-vi'.format(ALEPE_URL)


def parse_money(string):
    string = string.strip('R$ ')
    string = string.replace('.', '')
    string = string.replace(',', '.')
    return float(string)


def parse_date(string):
    return datetime.strptime(string, '%d/%m/%Y').date()


# https://stackoverflow.com/a/3422287
def merge_lists(l1, l2, key):
    merged = {}
    for item in l1 + l2:
        if item[key] in merged:
            merged[item[key]].update(item)
        else:
            merged[item[key]] = item
    return [val for (_, val) in merged.items()]


class ALEPE(BaseCollector):

    def __init__(self, collection_runs, debug_enabled=False):
        super(ALEPE, self).__init__(collection_runs, debug_enabled)

        self.institution, _ = Institution.objects.get_or_create(
            siglum='ALEPE',
            name=u'Assembléia Legislativa do Estado de Pernambuco',
        )

        self.legislature, _ = Legislature.objects.get_or_create(
            institution=self.institution,
            date_start=datetime(2015, 1, 1),
            date_end=datetime(2018, 12, 31),
        )

    def _get_options(self, tag_id, tag_value, data):
        options = data.find(id=tag_id).findAll('option')
        values = [
            {
                tag_value: x.get('value'),
                'name': x.text,
                'key': slugify(x.text)
            } for x in options
        ]
        values.pop(0)
        return values

    def update_legislators(self):
        data = BaseCollector.retrieve_uri(self, TRANSPARENCIA_URL)
        legislators_data = merge_lists(
            self._get_options('selectDep', 'id', data),
            self._get_options('field-deputados', 'url', data),
            'key',
        )
        for legislator_data in legislators_data:
            legislator_url = legislator_data.get('url')
            if not legislator_url:
                self.debug(
                    u'URL for Legislator {0} with id {1} does not exist'.format(
                        legislator_data['name'],
                        legislator_data['id'],
                    )
                )
                continue

            url = '{0}{1}'.format(ALEPE_URL, legislator_url)
            legislator_html = self.retrieve_uri(url)
            data_header = legislator_html.find('div', {'class': 'text'})
            name = data_header.find('h1').text
            party_siglum = data_header.find('span', {'class': 'subtitle'}).text
            resume = data_header.find('div', {'class': 'resume'}).text
            picture = '{0}{1}'.format(
                ALEPE_URL,
                legislator_html.find('figure').find('img')['src'],
            )

            legislator, created = Legislator.objects.get_or_create(name=name)
            if created:
                self.debug(u'New legislator: %s' % unicode(legislator))
            else:
                self.debug(u'Found existing legislator: %s' % unicode(legislator))

            legislator.about = resume
            legislator.picture = picture
            # FIXME
            # legislator.email = ''
            # legislator.alternative_names.append('')
            legislator.site = url
            legislator.save()

            party, _ = PoliticalParty.objects.get_or_create(siglum=party_siglum)

            self.mandate_for_legislator(
                legislator,
                party,
                original_id=legislator_data.get('id'),
            )

    def update_data(self):
        self.collection_run = self.create_collection_run(self.legislature)
        mandates = self.legislature.mandate_set.all()
        year_start = self.legislature.date_start.year
        year_end = self.legislature.date_end.year
        for year in range(year_start, year_end + 1):
            self.debug(u'Updating data for year {0}'.format(year))
            for month in range(1, 13):
                today = datetime.now()
                if today.year == year and month > today.month:
                    continue

                self.debug(u'Updating data for month {0}'.format(month))
                self._update_data_for_year(mandates, year, month)

    def _update_data_for_year(self, mandates, year, month):
        for mandate in mandates:
            url = '{0}/?dep={1}&ano={2}&mes={3}'.format(
                TRANSPARENCIA_URL,
                mandate.original_id,
                year,
                month,
            )
            expense_natures = {}
            expenses_data = self.retrieve_uri(url)
            natures = expenses_data.find(id='div-com-verba').findAll('h4')
            for nature in natures:
                # memory cache
                nature_name = nature.text.split('-')[1].strip()
                expense_nature = expense_natures.get(nature_name)
                if not expense_nature:
                    expense_nature, _ = ExpenseNature.objects.get_or_create(
                        name=nature_name,
                    )
                    expense_natures[nature_name] = expense_nature

                my_table = nature.findNextSibling().find('table')
                tds = my_table.findAll('td')

                date = parse_date(tds[0].text)
                cpf_cnpj = self.normalize_cnpj_or_cpf(tds[1].text)
                supplier_name = tds[2].text
                expensed = parse_money(tds[3].text)

                try:
                    supplier = Supplier.objects.get(identifier=cpf_cnpj)
                except Supplier.DoesNotExist:
                    supplier = Supplier(identifier=cpf_cnpj, name=supplier_name)
                    supplier.save()
                    self.debug(u'New supplier found: {0}'.format(unicode(supplier)))

                expense = ArchivedExpense(
                    original_id='',
                    number='',
                    nature=expense_nature,
                    date=date,
                    value=expensed,
                    expensed=expensed,
                    mandate=mandate,
                    supplier=supplier,
                    collection_run=self.collection_run,
                )
                expense.save()
                self.debug(u'New expense found: {0}'.format(unicode(expense)))
