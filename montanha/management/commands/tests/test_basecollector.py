# -*- coding: utf-8 -*-
#
# Copyright (©) 2016, Marcelo Jorge Vieira <metal@alucinados.com>
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

import time
from datetime import datetime, timedelta
from StringIO import StringIO

import requests
from django.test import TestCase
from mock import patch, Mock, call

from montanha.models import ArchivedExpense
from montanha.management.commands.collectors.basecollector import BaseCollector
from montanha.tests.fixtures import (
    LegislatureFactory, ArchivedExpenseFactory, CollectionRunFactory,
    MandateFactory, LegislatorFactory, PoliticalPartyFactory, SupplierFactory,
)


class BaseCollectorTestCase(TestCase):

    def setUp(self):
        self.base_collector = BaseCollector([], False)
        self.base_collector.default_timeout = 0.001
        self.base_collector.max_tries = 3
        self.base_collector.try_again_timer = 0.001

        date_start = datetime.now()
        date_end = date_start + timedelta(days=365 * 4)
        self.legislature = LegislatureFactory.create(
            date_start=date_start, date_end=date_end
        )
        self.mandate = MandateFactory.create(
            legislature=self.legislature,
            date_start=date_start,
            date_end=date_end
        )
        self.base_collector.legislature = self.legislature


class BaseCollectorNormalizeCnpjOrCpfTestCase(BaseCollectorTestCase):

    def test_with_cpf(self):
        cpf = self.base_collector.normalize_cnpj_or_cpf('012.345.678-90')
        self.assertEqual(cpf, '01234567890')

    def test_with_cnpj(self):
        cnpj = self.base_collector.normalize_cnpj_or_cpf('01.234.567/0001-89')
        self.assertEqual(cnpj, '01234567000189')


class BaseCollectorGetOrCreateSupplierTestCase(BaseCollectorTestCase):

    def test_get_supplier(self):
        SupplierFactory.create(identifier='01234567890')
        supplier = self.base_collector.get_or_create_supplier('012.345.678-90')
        self.assertEqual(supplier.identifier, '01234567890')

    def test_create_supplier(self):
        supplier = self.base_collector.get_or_create_supplier(
            '01.234.567/0001-89', 'Test Supplier'
        )
        self.assertEqual(supplier.identifier, '01234567000189')
        self.assertEqual(supplier.name, 'Test Supplier')


class BaseCollectorPostProcessUriTestCase(BaseCollectorTestCase):

    def test_post_process_uri(self):
        html = '<html><p>test</p></html>'
        data = self.base_collector.post_process_uri(html)
        self.assertEqual(str(data), html)


class BaseCollectorRetrieveUriTestCase(BaseCollectorTestCase):

    @patch('requests.get')
    def test_with_status_not_found(self, mock_get):
        mock_get.return_value.status_code = 404

        with self.assertRaises(Exception):
            data = self.base_collector.retrieve_uri('http://olhoneles.org')
            self.assertEqual(data, None)

    @patch('requests.get')
    def test_with_connection_error(self, mock_get):
        mock_get.side_effect = requests.exceptions.ConnectionError

        with self.assertRaises(RuntimeError) as e:
            self.base_collector.retrieve_uri('http://olhoneles.org')

        self.assertEqual(
            e.exception.message,
            'Error: Unable to retrieve http://olhoneles.org; Tried 3 times.'
        )

    @patch('requests.get')
    def test_with_post_process_false_return_content_true(self, mock_get):
        mock_get.return_value.status_code = 200
        mock_get.return_value.content = '<html><p>test</p></html>'

        data = self.base_collector.retrieve_uri(
            'http://olhoneles.org', post_process=False, return_content=True
        )
        self.assertEqual(str(data), '<html><p>test</p></html>')

    @patch('requests.get')
    def test_post_process_false_return_content_false(self, mock_get):
        mock_get.return_value.status_code = 200
        mock_get.return_value.text = '<html><p>test</p></html>'

        data = self.base_collector.retrieve_uri(
            'http://olhoneles.org', post_process=False, return_content=False
        )
        self.assertEqual(str(data), '<html><p>test</p></html>')

    @patch('requests.get')
    def test_force_encoding_true(self, mock_get):
        mock_get.return_value.text = '<html><p>test</p></html>'
        mock_get.return_value.status_code = 200

        self.base_collector.retrieve_uri(
            'http://olhoneles.org', force_encoding='utf-8'
        )
        self.assertEqual(mock_get.return_value.encoding, 'utf-8')

    @patch('requests.get')
    def test_via_get(self, mock_get):
        mock_get.return_value.text = '<html><p>test</p></html>'
        mock_get.return_value.status_code = 200

        data = self.base_collector.retrieve_uri('http://olhoneles.org')
        self.assertEqual(str(data), '<html><p>test</p></html>')

    @patch('requests.post')
    def test_via_post(self, mock_post):
        mock_post.return_value.text = '<html><p>test</p></html>'
        mock_post.return_value.status_code = 200

        month = {'month': 11}
        data = self.base_collector.retrieve_uri(
            'http://olhoneles.org', data=month
        )
        self.assertEqual(str(data), '<html><p>test</p></html>')


class BaseCollectorCreateCollectionRunTestCase(BaseCollectorTestCase):

    def test_with_new_collection_run(self):
        collection_run = self.base_collector.create_collection_run(self.legislature)

        self.assertEqual(self.base_collector.collection_runs[0], collection_run)
        self.assertEqual(collection_run.legislature, self.legislature)
        self.assertEqual(str(collection_run.date), str(datetime.now().date()))
        self.assertEqual(collection_run.committed, False)

    def test_with_exists_collection_run(self):
        collection_run = CollectionRunFactory.create(legislature=self.legislature)
        ArchivedExpenseFactory.create(collection_run=collection_run)

        self.assertEqual(ArchivedExpense.objects.count(), 1)
        self.base_collector.create_collection_run(self.legislature)
        self.assertEqual(ArchivedExpense.objects.count(), 0)


class BaseCollectorUpdateDataTestCase(BaseCollectorTestCase):

    def test_update_data_for_year_was_called(self):
        self.base_collector.update_data_for_year = Mock()

        self.base_collector.update_data()

        self.assertEqual(self.base_collector.update_data_for_year.call_count, 1)


class BaseCollectorUpdateDataForYearTestCase(BaseCollectorTestCase):

    def test_update_data_for_year_was_called(self):
        self.base_collector.update_data_for_month = Mock()

        self.base_collector.update_data_for_year(self.mandate, 2016)

        self.assertEqual(self.base_collector.update_data_for_month.call_count, 12)


class BaseCollectorMandateForLegislatorTestCase(BaseCollectorTestCase):

    def test_create_new_mandate(self):
        legislator = LegislatorFactory.create()
        political_party = PoliticalPartyFactory.create()

        mandate = self.base_collector.mandate_for_legislator(legislator, political_party)

        self.assertNotEqual(mandate, self.mandate)

    def test_get_mandate(self):
        legislator = LegislatorFactory.create()
        political_party = PoliticalPartyFactory.create()

        date_start = datetime.now()
        date_end = date_start + timedelta(days=365 * 4)

        self.mandate = MandateFactory.create(
            legislature=self.legislature,
            date_start=date_start,
            date_end=date_end,
            legislator=legislator,
        )

        mandate = self.base_collector.mandate_for_legislator(legislator, political_party)
        self.assertEqual(mandate, self.mandate)

    def test_set_original_id(self):
        legislator = LegislatorFactory.create()
        political_party = PoliticalPartyFactory.create()

        mandate = self.base_collector.mandate_for_legislator(
            legislator, political_party, original_id=123
        )

        self.assertEqual(mandate.original_id, 123)


class BaseCollectorDebugTestCase(BaseCollectorTestCase):

    @patch('time.time')
    def test_debug(self, mock_time):
        mock_time.return_value = time.mktime(datetime(2016, 12, 18).timetuple())
        self.base_collector.logfile = Mock()

        self.base_collector.debug('test')

        self.assertEqual(
            self.base_collector.logfile.mock_calls[0],
            call.write('2016-12-18:00:00:00 test\n')
        )

    def test_with_debug_enabled(self):
        self.base_collector.debug_enabled = True

        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            self.base_collector.debug('debug test')
            self.assertEqual(mock_stdout.getvalue(), 'debug test\n')


class BaseCollectorNormalizePartyNameTestCase(BaseCollectorTestCase):

    def test_normalize_party_name(self):
        name = self.base_collector.normalize_party_name('PCdoB')
        self.assertEqual(name, 'PC do B')
