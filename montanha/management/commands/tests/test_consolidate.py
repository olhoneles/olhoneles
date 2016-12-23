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

from datetime import datetime, timedelta, date

from mock import patch, call
from django.test import TestCase
from django.core.management import call_command

from montanha.management.commands.consolidate import Command
from montanha.models import (
    PerNature, PerNatureByYear, PerNatureByMonth, PerLegislator,
    BiggestSupplierForYear
)
from montanha.tests.fixtures import (
    InstitutionFactory, LegislatureFactory, PerNatureFactory,
    PerNatureByYearFactory, PerNatureByMonthFactory, ExpenseFactory,
    MandateFactory, PerLegislatorFactory, BiggestSupplierForYearFactory,
    SupplierFactory
)


class ConsolidateCommandsTestCase(TestCase):

    def setUp(self):
        self.siglums = ['ALMG', 'ALGO']
        self.institutions = {}
        self.legislatures = {}
        for siglum in self.siglums:
            institution = InstitutionFactory.create(name=siglum, siglum=siglum)
            self.institutions.update({siglum: institution})
            date_start = date(2016, 01, 01)
            date_end = date_start + timedelta(days=365 * 4)
            legislature = LegislatureFactory.create(
                date_start=date_start,
                date_end=date_end,
                institution=institution
            )
            self.legislatures.update({siglum: legislature})

    @patch.object(Command, 'per_legislator')
    @patch.object(Command, 'per_nature')
    def test_without_instituiton(self, per_nature_mock, per_legislator_mock):
        call_command('consolidate')

        per_nature_mock.assert_not_called()
        per_legislator_mock.assert_not_called()

    @patch.object(Command, 'per_legislator')
    @patch.object(Command, 'per_nature')
    def test_with_exist_instituiton(self, per_nature_mock, per_legislator_mock):
        call_command('consolidate', 'ALMG')

        per_nature_mock.assert_called_with(self.institutions['ALMG'])
        per_legislator_mock.assert_called_with(self.institutions['ALMG'])

    @patch.object(Command, 'per_legislator')
    @patch.object(Command, 'per_nature')
    def test_with_exist_lowercase_instituiton(self, per_nature_mock, per_legislator_mock):
        call_command('consolidate', 'almg')

        per_nature_mock.assert_called_with(self.institutions['ALMG'])
        per_legislator_mock.assert_called_with(self.institutions['ALMG'])

    @patch.object(Command, 'per_legislator')
    @patch.object(Command, 'per_nature')
    def test_with_two_exist_instituitons(self, per_nature_mock, per_legislator_mock):
        call_command('consolidate', 'ALMG', 'ALGO')

        self.assertEqual(
            per_nature_mock.mock_calls,
            [call(self.institutions['ALMG']), call(self.institutions['ALGO'])]
        )
        self.assertEqual(
            per_legislator_mock.mock_calls,
            [call(self.institutions['ALMG']), call(self.institutions['ALGO'])]
        )

    @patch.object(Command, 'per_legislator')
    @patch.object(Command, 'per_nature')
    def test_with_invalid_instituiton(self, per_nature_mock, per_legislator_mock):
        call_command('consolidate', 'invalid-instituiton')

        per_nature_mock.assert_not_called()
        per_legislator_mock.assert_not_called()

    @patch.object(Command, 'agnostic')
    @patch.object(Command, 'per_legislator')
    @patch.object(Command, 'per_nature')
    def test_with_agnostic(self, per_nature_mock, per_legislator_mock, agnostic_mock):
        call_command('consolidate', '--agnostic')

        per_nature_mock.assert_not_called()
        per_legislator_mock.assert_not_called()
        agnostic_mock.assert_called_once()


class ConsolidateCommandsBaseTestCase(ConsolidateCommandsTestCase):

    def setUp(self):
        super(ConsolidateCommandsBaseTestCase, self).setUp()
        self.institutions_siglum = 'ALMG'
        self.legislature = self.legislatures[self.institutions_siglum]
        self.mandate = MandateFactory.create(
            legislature=self.legislature,
            date_start=self.legislature.date_start,
            date_end=self.legislature.date_end,
        )


class ConsolidateCommandsPerNatureTestCase(ConsolidateCommandsBaseTestCase):

    def test_per_nature_remove_old_data(self):
        institution = self.institutions[self.institutions_siglum]
        PerNatureFactory.create(
            institution=institution,
            legislature=self.legislatures[self.institutions_siglum],
        )
        PerNatureByYearFactory.create(institution=institution)
        PerNatureByMonthFactory.create(institution=institution)

        call_command('consolidate', self.institutions_siglum)

        per_nature = PerNature.objects.count()
        by_year = PerNatureByYear.objects.count()
        by_month = PerNatureByMonth.objects.count()

        self.assertEqual(per_nature, 0)
        self.assertEqual(by_year, 0)
        self.assertEqual(by_month, 0)

    def test_per_nature_totals(self):
        date = datetime.today() + timedelta(days=2)
        ExpenseFactory.create(mandate=self.mandate, date=date, expensed=10, value=10)
        date = datetime.today() + timedelta(days=40)
        ExpenseFactory.create(mandate=self.mandate, date=date, expensed=5, value=5)

        call_command('consolidate', self.institutions_siglum)

        per_nature = PerNature.objects.all()
        self.assertEqual(len(per_nature), 4)
        self.assertEqual(per_nature[0].legislature, None)
        self.assertEqual(per_nature[0].expensed, 10)
        self.assertEqual(per_nature[1].legislature, self.legislature)
        self.assertEqual(per_nature[1].expensed, 10)
        self.assertEqual(per_nature[2].legislature, None)
        self.assertEqual(per_nature[2].expensed, 5)
        self.assertEqual(per_nature[3].legislature, self.legislature)
        self.assertEqual(per_nature[3].expensed, 5)

    def test_per_nature_by_month_totals(self):
        date = self.legislature.date_start
        ExpenseFactory.create(mandate=self.mandate, date=date, expensed=7, value=7)
        date = date + timedelta(days=40)
        ExpenseFactory.create(mandate=self.mandate, date=date, expensed=5, value=5)

        call_command('consolidate', self.institutions_siglum)

        per_nature_by_month = PerNatureByMonth.objects.all()
        self.assertEqual(len(per_nature_by_month), 2)
        self.assertEqual(per_nature_by_month[0].expensed, 0)
        self.assertEqual(per_nature_by_month[1].expensed, 5)

    def test_per_nature_by_year_totals(self):
        date = self.legislature.date_start
        ExpenseFactory.create(mandate=self.mandate, date=date, expensed=3, value=3)
        ExpenseFactory.create(mandate=self.mandate, date=date, expensed=5, value=5)

        call_command('consolidate', self.institutions_siglum)

        per_nature_by_year = PerNatureByYear.objects.all()
        self.assertEqual(len(per_nature_by_year), 2)
        self.assertEqual(per_nature_by_year[0].expensed, 5)
        self.assertEqual(per_nature_by_year[1].expensed, 3)


class ConsolidateCommandsPerLegislatorTestCase(ConsolidateCommandsBaseTestCase):

    def test_per_legislator_remove_old_data(self):
        institution = self.institutions[self.institutions_siglum]
        PerLegislatorFactory.create(institution=institution)

        call_command('consolidate', self.institutions_siglum)

        per_legislator = PerLegislator.objects.count()
        self.assertEqual(per_legislator, 0)

    def test_per_legislator_totals(self):
        ExpenseFactory.create(mandate=self.mandate, expensed=10, value=10)

        call_command('consolidate', self.institutions_siglum)

        per_legislator = PerLegislator.objects.all()
        self.assertEqual(len(per_legislator), 2)
        self.assertEqual(per_legislator[0].legislature, self.legislature)
        self.assertEqual(per_legislator[0].expensed, 10)
        self.assertEqual(per_legislator[1].legislature, None)
        self.assertEqual(per_legislator[1].expensed, 10)


class ConsolidateCommandsAgnosticTestCase(ConsolidateCommandsBaseTestCase):

    def test_agnostic_remove_old_data(self):
        BiggestSupplierForYearFactory.create(year=datetime.now().year)

        call_command('consolidate', '--agnostic')

        biggest_supplier = BiggestSupplierForYear.objects.count()
        self.assertEqual(biggest_supplier, 0)

    def test_agnostic_with_same_supplier(self):
        supplier = SupplierFactory.create()
        ExpenseFactory.create(
            supplier=supplier, mandate=self.mandate, value=10, expensed=10
        )
        ExpenseFactory.create(
            supplier=supplier, mandate=self.mandate, value=12, expensed=12
        )

        call_command('consolidate', '--agnostic')

        biggest_supplier = BiggestSupplierForYear.objects.all()
        self.assertEqual(len(biggest_supplier), 1)
        self.assertEqual(biggest_supplier[0].expensed, 22)

    def test_agnostic_with_different_suppliers(self):
        ExpenseFactory.create(mandate=self.mandate, value=10, expensed=10)
        ExpenseFactory.create(mandate=self.mandate, value=12, expensed=12)

        call_command('consolidate', '--agnostic')

        biggest_supplier = BiggestSupplierForYear.objects.all()
        self.assertEqual(len(biggest_supplier), 2)
        self.assertEqual(biggest_supplier[0].expensed, 12)
        self.assertEqual(biggest_supplier[1].expensed, 10)
