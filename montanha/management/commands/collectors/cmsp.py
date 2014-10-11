# -*- coding: utf-8 -*-
#
# Copyright (©) 2013 Marcelo Jorge Vieira <metal@alucinados.com>
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

import os
import re
import urllib
from datetime import datetime
from django.core.files import File

from basecollector import BaseCollector
from montanha.models import *


def parse_money(string):
    string = string.replace('.', '')
    string = string.replace(',', '.')
    return float(string)


def parse_date(string):
    return datetime.strptime(string, '%d/%m/%Y').date()


def parse_cmsp_date(month, year):
    day = '01'
    return parse_date(day + '/' + month + '/' + year)


class CMSP(BaseCollector):
    def __init__(self, collection_runs, debug_enabled=False):
        super(CMSP, self).__init__(collection_runs, debug_enabled)

        institution, institution_created = Institution.objects.get_or_create(
            siglum='CMSP',
            name=u'Câmara Municipal de São Paulo')

        self.institution = institution

    def _normalize_party_siglum(self, siglum):
        names_map = {
            'DEMOCRATAS': 'DEM',
        }
        return names_map.get(siglum, siglum)

    def retrieve_expenses(self, month, year):
        uri = 'http://www2.camara.sp.gov.br/SAEG/%s%s.xml' % (year, month)
        return BaseCollector.retrieve_uri(self, uri, force_encoding='utf-8')

    def retrieve_legislators(self):
        uri = 'http://www1.camara.sp.gov.br/vereadores_joomla.asp'
        return BaseCollector.retrieve_uri(self, uri)

    def retrieve_legislator(self, link):
        uri = 'http://www1.camara.sp.gov.br/%s' % link
        return BaseCollector.retrieve_uri(self, uri)

    def add_legislator(self, name):
        legislator, created = Legislator.objects.get_or_create(name=name)

        if created:
            self.debug(u'New legislator found: %s' % legislator)
        else:
            self.debug(u'Found existing legislator: %s' % legislator)

        return legislator

    def process_legislators(self, legislature):
        legislators = self.retrieve_legislators()
        if not legislators:
            return

        links = legislators.findAll(
            'a',
            href=re.compile('^vereador_joomla2.asp\?vereador='))

        for link in links:
            href = link.get('href')
            html_legislator = self.retrieve_legislator(href)
            if not html_legislator:
                continue

            url, code = href.split('=', 1)
            name = html_legislator.find(id='nome_vereador').getText()

            legislator = self.add_legislator(name)

            legislator_img = html_legislator.find(
                'img',
                src=re.compile('imgs/fotos/'))

            if legislator_img:
                legislator_img_src = legislator_img.get('src')

                legislator_img_url = 'http://www1.camara.sp.gov.br/%s' % (
                    legislator_img_src)

                result = urllib.urlretrieve(legislator_img_url)

                legislator.picture.save(
                    os.path.basename(legislator_img_url), File(open(result[0])))

                legislator.save()

                self.debug('Updating legislator picture.')

            try:
                mandate = Mandate.objects.get(
                    legislator=legislator,
                    date_start=legislature.date_start,
                    legislature=legislature)
                self.debug(u'Found existing Mandate: %s' % mandate)
            except Mandate.DoesNotExist:
                mandate = Mandate(
                    legislator=legislator,
                    date_start=legislature.date_start,
                    legislature=legislature)
                mandate.save()
                self.debug(u'New Mandate found: %s' % mandate)

            party_name = html_legislator.find(
                'img',
                src=re.compile('imgs/Partidos'))

            party_name = party_name.parent.parent.find('font', size='2')
            party_name = party_name.getText()
            party_siglum = party_name[party_name.find('(')+1:party_name.find(')')]

            if 'Vereadores Licenciados' not in party_siglum:
                party_siglum = self._normalize_party_siglum(party_siglum)
                party, party_created = PoliticalParty.objects.get_or_create(
                    siglum=party_siglum)

                mandate.party = party
                mandate.save()
                self.debug('Updating legislator party: %s' % party_siglum)

    def process_expenses(self, month, year, legislature, collection_run):
        data = self.retrieve_expenses(month, year)
        if not data:
            return

        for x in data.findAll('g_deputado'):
            name = x.find('nm_deputado').getText().capitalize()
            legislator = self.add_legislator(name)

            try:
                mandate = Mandate.objects.get(
                    legislator=legislator,
                    date_start=legislature.date_start,
                    legislature=legislature)
                self.debug(u'Found existing Mandate: %s' % mandate)
            except Mandate.DoesNotExist:
                mandate = Mandate(
                    legislator=legislator,
                    date_start=legislature.date_start,
                    legislature=legislature)
                mandate.save()
                self.debug(u'New Mandate found: %s' % mandate)

            expense_type = x.find('list_g_tipo_despesa')

            for i in expense_type.findAll('g_tipo_despesa'):
                nature_text = i.find('nm_tipo_despesa').getText()
                try:
                    nature_text = nature_text.split('-', 1)[1].strip()
                except IndexError:
                    pass

                nature_text = nature_text.capitalize()

                ignore_list = [u'total', u'TOTAL', u'utilizado até 30/11/07']
                ignore_matches = [s for s in ignore_list if s in nature_text]
                if ignore_matches:
                    continue

                nature, nature_created = ExpenseNature.objects.get_or_create(
                    name=nature_text)

                if nature_created:
                    self.debug(u'New ExpenseNature found: %s' % nature)
                else:
                    self.debug(u'Found existing ExpenseNature: %s' % nature)

                m_month = i.find('nr_mes_ref').getText()
                m_year = i.find('nr_ano_ref').getText()
                date = parse_cmsp_date(m_month, m_year)

                for j in i.findAll('g_beneficiario'):
                    supplier_name = j.find('nm_beneficiario').getText()
                    supplier_name = supplier_name.capitalize()
                    cnpj = self.normalize_cnpj_or_cpf(j.find('nr_cnpj').getText())

                    if not cnpj and not supplier_name:
                        continue

                    try:
                        supplier = Supplier.objects.get(identifier=cnpj)
                        supplier_created = False
                    except Supplier.DoesNotExist:
                        supplier = Supplier(identifier=cnpj, name=supplier_name)
                        supplier.save()
                        supplier_created = True

                    if supplier_created:
                        self.debug(u'New Supplier found: %s' % supplier)
                    else:
                        self.debug(u'Found existing supplier: %s' % supplier)

                    expensed = parse_money(j.find('vl_desp').getText())

                    expense = ArchivedExpense(number='None',
                                              nature=nature,
                                              date=date,
                                              expensed=expensed,
                                              mandate=mandate,
                                              supplier=supplier,
                                              collection_run=collection_run)
                    expense.save()

                    self.debug(u'New expense found: %s' % expense)

    def get_legislature(self, year):
        start_year = end_year = year

        if year >= 2013 and year <= 2016:
            start_year = 2013
            end_year = 2016

        if year >= 2009 and year <= 2012:
            start_year = 2009
            end_year = 2012

        if year >= 2005 and year <= 2008:
            start_year = 2005
            end_year = 2008

        legislature, created = Legislature.objects.get_or_create(
            institution=self.institution,
            date_start=datetime(start_year, 1, 1),
            date_end=datetime(end_year, 12, 31))

        if created:
            self.debug(u'New Legislature found: %s' % legislature)
        else:
            self.debug(u'Found existing legislature: %s' % legislature)

        return legislature

    def process_all_expenses(self):
        for year in xrange(2007, 2014):
            legislature = self.get_legislature(year)
            collection_run = self.create_collection_run(legislature)
            for m in xrange(1, 13):
                month = '%02d' % m
                self.debug('Adding expenses from %s/%s' % (month, year))
                self.process_expenses(month, year, legislature, collection_run)

    def process_current_legislators(self):
        current_legislature = self.get_legislature(2013)
        self.process_legislators(current_legislature)

    def process_all_legislators(self):
        import urllib2
        uri = 'http://www2.camara.sp.gov.br/Dados_abertos/vereador/vereador.txt'

        contents = urllib2.urlopen(uri)

        for line in contents:

            try:
                line = line.decode('utf-8')
            except UnicodeDecodeError:
                try:
                    line = line.decode('iso-8859-1')
                except Exception:
                    pass

            row = line.split('#')
            if len(row) > 1:
                name = row[1]
                nickname = row[2]

                if nickname:
                    legislator = self.add_legislator(nickname)
                else:
                    legislator = self.add_legislator(name)

                aa = re.search('\^\p([^\^|%]*)(\^|%)', row[7])
                if aa:
                    party_siglum = aa.group(1)
                else:
                    pass

                try:
                    date_start_re = re.search('\^\i([^\^|%]*)(\^|%)', row[7])
                    start_year = int(date_start_re.group(1).split('/')[2])
                    date_start = datetime(start_year, 1, 1)
                except IndexError:
                    continue

                legislature = self.get_legislature(start_year)

                mandate, mandate_created = Mandate.objects.get_or_create(
                    legislator=legislator,
                    date_start=legislature.date_start,
                    legislature=legislature)

                if mandate_created:
                    self.debug(u'New Mandate found: %s' % mandate)
                else:
                    self.debug(u'Found existing Mandate: %s' % mandate)

                if party_siglum and 'Sem' or 'Vereaores' not in party_siglum:
                    party, party_created = PoliticalParty.objects.get_or_create(
                        siglum=party_siglum)

                    mandate.party = party
                    mandate.save()
                    self.debug('Updating legislator party: %s' % party)

    def update_data(self):
        self.process_all_legislators()
        self.process_current_legislators()
        self.process_all_expenses()
