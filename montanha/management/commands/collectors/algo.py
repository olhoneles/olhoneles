# -*- coding: utf-8 -*-
#
# Copyright (©) 2010-2013 Estêvão Samuel Procópio
# Copyright (©) 2010-2013 Gustavo Noronha Silva
# Copyright (©) 2013 Marcelo Jorge Vieira
# Copyright (©) 2014 Wilson Pinto Júnior
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
import os
import rows
import operator
import json
from io import BytesIO

from cachetools import Cache, cachedmethod
from cStringIO import StringIO

from basecollector import BaseCollector
from django.core.files import File
from datetime import datetime

from montanha.models import (
    Institution, Legislature, PoliticalParty, Legislator, ExpenseNature,
    Supplier, ArchivedExpense, Mandate
)


class ALGO(BaseCollector):
    TITLE_REGEX = re.compile(r'\d+ - (.*)')

    def __init__(self, *args, **kwargs):
        super(ALGO, self).__init__(*args, **kwargs)

        self.base_url = 'http://al.go.leg.br'

        try:
            institution = Institution.objects.get(siglum='ALGO')
        except Institution.DoesNotExist:
            institution = Institution(siglum='ALGO', name=u'Assembléia Legislativa do Estado de Goiás')
            institution.save()

        try:
            self.legislature = Legislature.objects.all().filter(institution=institution).order_by('-date_start')[0]
        except IndexError:
            self.legislature = Legislature(institution=institution,
                                           date_start=datetime(2015, 1, 1),
                                           date_end=datetime(2018, 12, 31))
            self.legislature.save()

        self.list_of_legislators_cache = Cache(1024)
        self.expenses_nature_cached = {}

    def _normalize_party_siglum(self, siglum):
        names_map = {
            'SDD': 'Solidariedade',
        }
        return names_map.get(siglum, siglum)

    def update_legislators(self):
        url = self.base_url + '/deputado/'
        html = BaseCollector.retrieve_uri(self, url, post_process=False, force_encoding='utf-8')

        rows_xpath = u'//tbody/tr'
        fields_xpath = {
            u'nome': u'./td[position()=1]/a/text()',
            u'url': u'./td[position()=1]/a/@href',
            u'party': u'./td[position()=2]/text()',
            u'telefone': u'./td[position()=3]/text()',
            u'fax': u'./td[position()=4]/text()',
            u'email': u'./td[position()=5]/a[position()=1]/img/@title',
        }
        table = rows.import_from_xpath(BytesIO(html.encode('utf-8')), rows_xpath, fields_xpath)

        url_regex = re.compile(r'.*id/(\d+)')
        email_regex = re.compile(r'Email: (.*)')

        for row in table:
            _id = url_regex.match(row.url).group(1)
            email = None

            if row.email:
                email = email_regex.match(row.email).group(1).strip()

            party_siglum = self._normalize_party_siglum(row.party)
            party, party_created = PoliticalParty.objects.get_or_create(
                siglum=party_siglum
            )

            self.debug("New party: %s" % unicode(party))

            legislator, created = Legislator.objects.get_or_create(name=row.nome)

            legislator.site = self.base_url + row.url
            legislator.email = email
            legislator.save()

            if created:
                self.debug("New legislator: %s" % unicode(legislator))
            else:
                self.debug("Found existing legislator: %s" % unicode(legislator))

            self.mandate_for_legislator(legislator, party, original_id=_id)

    @classmethod
    def parse_title(self, title):
        if '-' in title:
            match = self.TITLE_REGEX.search(title)

            if match:
                return match.group(1).encode('utf-8')

        return title.encode('utf-8')

    MONEY_RE = re.compile(r'([0-9.,]+)[,.]([0-9]{2})$')

    @classmethod
    def parse_money(self, value):
        match = self.MONEY_RE.search(value)

        if match:
            return float('%s.%s' % (match.group(1).replace('.', '').replace(',', ''), match.group(2)))
        else:
            raise ValueError('Cannot convert %s to float (money)' % value)

    def get_parlamentar_id(self, year, month, name):
        legislators = self.get_list_of_legislators(year, month)
        legislators = [i for i in legislators if i['nome'] == name]

        if not legislators:
            return

        return legislators[0]['id']

    @cachedmethod(operator.attrgetter('list_of_legislators_cache'))
    def get_list_of_legislators(self, year, month):
        url = '%s/transparencia/verbaindenizatoria/listardeputados?ano=%d&mes=%d' % (
            self.base_url,
            year,
            month,
        )
        data = json.loads(self.retrieve_uri(url, force_encoding='utf8').text)
        return data['deputados']

    def find_data_for_month(self, mandate, year, month):
        parlamentar_id = self.get_parlamentar_id(year, month, mandate.legislator.name)

        if not parlamentar_id:
            self.debug(
                "Failed to discover parlamentar_id for year=%d, month=%d, legislator=%s" %
                year, month, mandate.legislator.name,
            )
            raise StopIteration

        url = '%s/transparencia/verbaindenizatoria/exibir?ano=%d&mes=%d&parlamentar_id=%s' % (
            self.base_url, year, month, parlamentar_id)
        data = self.retrieve_uri(url, force_encoding='utf8')

        if u'parlamentar não prestou contas para o mês' in data.text:
            self.debug("not found data for: %s -> %d/%d" % (
                unicode(mandate.legislator), year, month))
            raise StopIteration

        container = data.find('div', id='verba')

        if not container:
            self.debug('div#verba not found')

        table = container.find('table', recursive=False)

        if not table:
            self.debug("table.tabela-verba-indenizatoria not found")
            raise StopIteration

        group_trs = table.findAll('tr', {'class': 'verba_titulo'})

        for tr in group_trs:
            budget_title = self.parse_title(tr.text)
            budget_subtitle = None

            while True:
                tr = tr.findNext('tr')

                if not tr:
                    break

                tr_class = tr.get('class')

                if tr.get('class') == 'verba_titulo':
                    break

                elif tr_class == 'info-detalhe-verba':
                    for data in self.parse_detale_verba(tr, budget_title, budget_subtitle):
                        yield data

                elif tr_class == 'subtotal':
                    continue

                elif len(tr.findAll('td')) == 3:
                    tds = tr.findAll('td')
                    budget_subtitle = self.parse_title(tds[0].text)

                    next_tr = tr.findNext('tr')
                    break_classes = ('subtotal', 'info-detalhe-verba', 'verba_titulo')

                    if next_tr.get('class') in break_classes:
                        continue

                    value_presented = self.parse_money(tds[1].text)
                    value_expensed = self.parse_money(tds[2].text)

                    if not value_expensed or not value_presented:
                        continue

                    data = {
                        'budget_title': budget_title,
                        'budget_subtitle': budget_subtitle,
                        'value_presented': value_presented,
                        'date': '1/%d/%d' % (month, year),
                        'value_expensed': value_expensed,
                        'number': 'Sem número'
                    }

                    self.debug(u'Generated JSON: %s' % data)

                    yield data

    def parse_detale_verba(self, elem, budget_title, budget_subtitle):
        rows_xpath = u'//tbody/tr'
        fields_xpath = {
            u'nome': u'./td[position()=1]/text()',
            u'cpf_cnpj': u'./td[position()=2]/text()',
            u'date': u'./td[position()=3]/text()',
            u'number': u'./td[position()=4]/text()',
            u'value_presented': u'./td[position()=5]/text()',
            u'value_expensed': u'./td[position()=6]/text()',
        }
        table = rows.import_from_xpath(
            BytesIO(str(elem)), rows_xpath, fields_xpath)
        for row in table:
            data = dict(row.__dict__)
            data.update({
                'budget_title': budget_title,
                'budget_subtitle': budget_subtitle,
                'cpf_cnpj': self.normalize_cnpj_or_cpf(row.cpf_cnpj),
                'value_presented': self.parse_money(row.value_presented),
                'value_expensed': self.parse_money(row.value_expensed),
            })
            self.debug(u'Generated JSON: %s' % data)

            yield data

    def get_or_create_expense_nature(self, name):
        if name not in self.expenses_nature_cached:
            try:
                nature = ExpenseNature.objects.get(name=name)
            except ExpenseNature.DoesNotExist:
                nature = ExpenseNature(name=name)
                nature.save()

            self.expenses_nature_cached[name] = nature

        return self.expenses_nature_cached[name]

    def update_data_for_month(self, mandate, year, month):
        for data in self.find_data_for_month(mandate, year, month):
            nature = self.get_or_create_expense_nature(data['budget_title'] + ': ' + data['budget_subtitle'])

            name = data.get('nome') or 'Sem nome'
            cpf_cnpj = data.get('cpf_cnpj') or 'Sem CPF/CNPJ (%s)' % name

            try:
                supplier = Supplier.objects.get(identifier=cpf_cnpj)
            except Supplier.DoesNotExist:
                supplier = Supplier(identifier=cpf_cnpj, name=name)
                supplier.save()

            date = datetime.strptime(data['date'], '%d/%m/%Y')
            expense = ArchivedExpense(
                number=data['number'],
                nature=nature,
                date=date,
                value=data['value_presented'],
                expensed=data['value_expensed'],
                mandate=mandate,
                supplier=supplier,
                collection_run=self.collection_run,
            )

            expense.save()

    def update_images(self):
        mandates = Mandate.objects.filter(legislature=self.legislature, legislator__picture='')

        headers = {
            'Referer': self.base_url + '/deputado/',
            'Origin': self.base_url,
        }
        deputado_data = self.retrieve_uri(self.base_url + '/deputado/', headers=headers)

        for mandate in mandates:
            leg = mandate.legislator
            found_text = deputado_data.find(text=re.compile(leg.name))

            if not found_text:
                self.debug('Legislator not found in page: %s' % mandate.legislator.name)
                continue

            tr = found_text.findParents('tr')[0]
            tds = tr.findAll('td')

            detail_path = tds[0].find('a')['href']
            detail_url = self.base_url + detail_path
            detail_data = self.retrieve_uri(detail_url, headers=headers)

            photo_container = detail_data.find('div', {'class': re.compile(r'foto')})
            photo_url = photo_container.find('img')['src']
            photo_data = self.retrieve_uri(self.base_url + photo_url, post_process=False, return_content=True)

            photo_buffer = StringIO(photo_data)
            photo_buffer.seek(0)

            leg.picture.save(os.path.basename(photo_url), File(photo_buffer))
            leg.save()

            self.debug('Saved %s Image URL: %s' % (leg.name, photo_url))

        else:
            self.debug('All legislators have photos')
