# -*- coding: utf-8 -*-
#
# Copyright (©) 2014, Marcelo Jorge Vieira <metal@alucinados.com>
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

from decimal import Decimal
from datetime import datetime
from random import randint

import factory

from montanha.models import (
    Institution, Legislature, ArchivedExpense, CollectionRun, Expense,
    ExpenseNature, Mandate, Supplier, PoliticalParty, Legislator, PerNature,
    PerNatureByYear, PerNatureByMonth, PerLegislator, BiggestSupplierForYear
)


class InstitutionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Institution

    name = factory.Sequence(lambda t: 'name-{0}'.format(t))
    siglum = factory.Sequence(lambda t: 'siglum-{0}'.format(t))


class LegislatureFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Legislature

    institution = factory.SubFactory(InstitutionFactory)
    original_id = factory.Sequence(lambda t: 'id-{0}'.format(t))
    date_start = factory.LazyFunction(datetime.now().date)
    date_end = factory.LazyFunction(datetime.now().date)


class CollectionRunFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = CollectionRun

    date = factory.LazyFunction(datetime.now().date)
    legislature = factory.SubFactory(LegislatureFactory)
    committed = False


class ExpenseNatureFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ExpenseNature


class SupplierFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Supplier

    name = factory.Sequence(lambda t: 'name-{0}'.format(t))
    identifier = factory.Sequence(lambda t: 'id-{0}'.format(t))


class LegislatorFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Legislator

    name = factory.Sequence(lambda t: 'name-{0}'.format(t))


class PoliticalPartyFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = PoliticalParty

    name = factory.Sequence(lambda t: 'name-{0}'.format(t))
    siglum = factory.Sequence(lambda t: 'siglum-{0}'.format(t))


class MandateFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Mandate

    original_id = factory.Sequence(lambda t: 'id-{0}'.format(t))
    legislator = factory.SubFactory(LegislatorFactory)
    legislature = factory.SubFactory(LegislatureFactory)
    date_start = factory.LazyFunction(datetime.now().date)
    date_end = factory.LazyFunction(datetime.now().date)
    party = factory.SubFactory(PoliticalPartyFactory)
    state = factory.Sequence(lambda t: 'state-{0}'.format(t))


class ArchivedExpenseFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ArchivedExpense

    collection_run = factory.SubFactory(CollectionRunFactory)
    original_id = factory.Sequence(lambda t: 'id-{0}'.format(t))
    number = factory.Sequence(lambda t: 'number-{0}'.format(t))
    date = factory.LazyFunction(datetime.now().date)
    nature = factory.SubFactory(ExpenseNatureFactory)
    mandate = factory.SubFactory(MandateFactory)
    supplier = factory.SubFactory(SupplierFactory)
    value = factory.LazyAttribute(lambda o: Decimal(randint(5, 100)))
    expensed = factory.LazyAttribute(lambda o: Decimal(randint(5, 100)))


class PerNatureFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = PerNature

    institution = factory.SubFactory(InstitutionFactory)
    legislature = factory.SubFactory(LegislatureFactory)
    date_start = factory.LazyFunction(datetime.now().date)
    date_end = factory.LazyFunction(datetime.now().date)
    nature = factory.SubFactory(ExpenseNatureFactory)
    expensed = factory.LazyAttribute(lambda o: Decimal(randint(5, 100)))


class PerNatureByYearFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = PerNatureByYear

    institution = factory.SubFactory(InstitutionFactory)
    nature = factory.SubFactory(ExpenseNatureFactory)
    expensed = factory.LazyAttribute(lambda o: Decimal(randint(5, 100)))
    year = factory.LazyAttribute(lambda o: datetime.now().year)


class PerNatureByMonthFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = PerNatureByMonth

    institution = factory.SubFactory(InstitutionFactory)
    date = factory.LazyFunction(datetime.now().date)
    nature = factory.SubFactory(ExpenseNatureFactory)
    expensed = factory.LazyAttribute(lambda o: Decimal(randint(5, 100)))


class PerLegislatorFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = PerLegislator

    institution = factory.SubFactory(InstitutionFactory)
    legislature = factory.SubFactory(LegislatureFactory)
    legislator = factory.SubFactory(LegislatorFactory)
    date_start = factory.LazyFunction(datetime.now().date)
    date_end = factory.LazyFunction(datetime.now().date)
    expensed = factory.LazyAttribute(lambda o: Decimal(randint(5, 100)))


class BiggestSupplierForYearFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = BiggestSupplierForYear

    supplier = factory.SubFactory(SupplierFactory)
    year = factory.LazyAttribute(lambda o: datetime.now().year)
    expensed = factory.LazyAttribute(lambda o: Decimal(randint(5, 100)))


class ExpenseFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Expense

    original_id = factory.Sequence(lambda t: 'id-{0}'.format(t))
    number = factory.Sequence(lambda t: 'number-{0}'.format(t))
    date = factory.LazyFunction(datetime.now().date)
    nature = factory.SubFactory(ExpenseNatureFactory)
    mandate = factory.SubFactory(MandateFactory)
    supplier = factory.SubFactory(SupplierFactory)
    value = factory.LazyAttribute(lambda o: Decimal(randint(5, 100)))
    expensed = factory.LazyAttribute(lambda o: Decimal(randint(5, 100)))
