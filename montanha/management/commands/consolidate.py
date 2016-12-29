# -*- coding: utf-8 -*-
#
# Copyright (©) 2014 Gustavo Noronha Silva
# Copyright (©) 2016 Marcelo Jorge Vieira
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

# This hack makes django less memory hungry (it caches queries when running
# with debug enabled.

import codecs
import sys
from datetime import date

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db.models import Sum

from montanha.models import (
    Institution, Expense, ExpenseNature, Legislator, Supplier, PerNature,
    PerNatureByYear, PerNatureByMonth, PerLegislator, BiggestSupplierForYear
)
from montanha.util import (
    filter_for_institution, get_date_ranges_from_data, ensure_years_in_range
)


settings.DEBUG = False
sys.stdout = codecs.getwriter("utf-8")(sys.stdout)
sys.stderr = codecs.getwriter("utf-8")(sys.stderr)


class Command(BaseCommand):
    help = "Collects data for a number of sources"
    institutions = []

    def add_arguments(self, parser):
        parser.add_argument('house', type=str, nargs='*', default='')
        parser.add_argument(
            '--agnostic',
            action='store_true',
            dest='agnostic',
            default=False,
        )

    def handle(self, *args, **options):
        if 'almg' in options.get('house'):
            self.institutions.append(Institution.objects.get(siglum='ALMG'))

        if 'algo' in options.get('house'):
            self.institutions.append(Institution.objects.get(siglum='ALGO'))

        if 'senado' in options.get('house'):
            self.institutions.append(Institution.objects.get(siglum='Senado'))

        if 'cmbh' in options.get('house'):
            self.institutions.append(Institution.objects.get(siglum='CMBH'))

        if 'cmsp' in options.get('house'):
            self.institutions.append(Institution.objects.get(siglum='CMSP'))

        if 'cdep' in options.get('house'):
            self.institutions.append(Institution.objects.get(siglum='CDEP'))

        for institution in self.institutions:
            print u'Consolidating data for %s' % (institution.name)
            self.per_nature(institution)
            self.per_legislator(institution)

        if options.get('agnostic'):
            self.agnostic()

    def per_nature(self, institution):
        PerNature.objects.filter(institution=institution).delete()
        PerNatureByYear.objects.filter(institution=institution).delete()
        PerNatureByMonth.objects.filter(institution=institution).delete()

        data = Expense.objects.all()
        data = filter_for_institution(data, institution)

        date_ranges = get_date_ranges_from_data(institution, data)

        data = data \
            .values('nature__id') \
            .annotate(expensed=Sum('expensed')) \
            .order_by('-expensed')

        years = [d.year for d in Expense.objects.dates('date', 'year')]
        years = ensure_years_in_range(date_ranges, years)

        per_natures_to_create = list()
        per_natures_by_year_to_create = list()
        per_natures_by_month_to_create = list()

        for item in data:
            # Totals
            nature = ExpenseNature.objects.get(id=item['nature__id'])
            p = PerNature(
                institution=institution,
                date_start=date_ranges['cdf'],
                date_end=date_ranges['cdt'],
                nature=nature,
                expensed=item['expensed']
            )
            per_natures_to_create.append(p)

            # Totals for Legislature
            per_natures_to_create += self._per_nature_total_for_legislature(
                institution, nature
            )

            # By Year
            year_to_create, month_to_create = self._per_nature_by_year(
                years, institution, nature
            )
            per_natures_by_year_to_create += year_to_create
            per_natures_by_month_to_create += month_to_create

        PerNature.objects.bulk_create(per_natures_to_create)
        PerNatureByMonth.objects.bulk_create(per_natures_by_month_to_create)
        PerNatureByYear.objects.bulk_create(per_natures_by_year_to_create)

    def _per_nature_total_for_legislature(self, institution, nature):
        per_natures_to_create = list()
        for legislature in institution.legislature_set.all():
            print u'[%s] Consolidating nature %s totals for legislature %d-%d…' % (
                institution.siglum,
                nature.name,
                legislature.date_start.year,
                legislature.date_end.year
            )

            legislature_data = Expense.objects \
                .filter(nature=nature) \
                .filter(mandate__legislature=legislature)

            legislature_ranges = get_date_ranges_from_data(institution, legislature_data)

            legislature_data = legislature_data \
                .values('nature__id') \
                .annotate(expensed=Sum('expensed')) \
                .order_by('-expensed')

            if legislature_data:
                legislature_data = legislature_data[0]
            else:
                legislature_data = dict(expensed='0.')

            p = PerNature(
                institution=institution,
                legislature=legislature,
                date_start=legislature_ranges['cdf'],
                date_end=legislature_ranges['cdt'],
                nature=nature,
                expensed=legislature_data['expensed']
            )
            per_natures_to_create.append(p)
        return per_natures_to_create

    def _per_nature_by_year(self, years, institution, nature):
        per_natures_by_year_to_create = list()
        per_natures_by_month_to_create = list()

        for year in years:
            print u'[%s] Consolidating nature %s totals for year %d…' % (
                institution.siglum, nature.name, year
            )

            year_data = Expense.objects \
                .filter(nature=nature) \
                .filter(date__year=year)

            year_data = filter_for_institution(year_data, institution)

            # By Month
            per_natures_by_month_to_create += self._per_nature_by_month(
                year_data, year, institution, nature
            )

            year_data = year_data \
                .values('nature__id') \
                .annotate(expensed=Sum("expensed"))

            if year_data:
                year_data = year_data[0]
            else:
                year_data = dict(expensed='0.')

            p = PerNatureByYear(
                institution=institution,
                year=year,
                nature=nature,
                expensed=float(year_data['expensed'])
            )
            per_natures_by_year_to_create.append(p)
        return per_natures_by_year_to_create, per_natures_by_month_to_create

    def _per_nature_by_month(self, year_data, year, institution, nature):
        per_natures_by_month_to_create = list()

        last_date = year_data and year_data.order_by('-date')[0].date or date.today()
        for month in range(1, 13):
            print u'[%s] Consolidating nature %s totals for %d-%d…' % (
                institution.siglum, nature.name, year, month
            )

            month_date = date(year, month, 1)

            if month_date >= last_date:
                break

            mdata = year_data.filter(date__month=month) \
                .values('nature__id') \
                .annotate(expensed=Sum('expensed')) \
                .order_by('-expensed')

            if mdata:
                mdata = mdata[0]
            else:
                mdata = dict(expensed='0.')

            p = PerNatureByMonth(
                institution=institution,
                date=month_date,
                nature=nature,
                expensed=float(mdata['expensed'])
            )
            per_natures_by_month_to_create.append(p)
        return per_natures_by_month_to_create

    def per_legislator(self, institution):
        PerLegislator.objects.filter(institution=institution).delete()

        data = Expense.objects.all()
        data = filter_for_institution(data, institution)

        date_ranges = get_date_ranges_from_data(institution, data)

        data = data \
            .values('mandate__legislator__id') \
            .annotate(expensed=Sum('expensed'))

        per_legislators_to_create = list()
        for item in data:
            legislator = Legislator.objects.get(id=int(item['mandate__legislator__id']))

            # Totals for Legislature
            for legislature in institution.legislature_set.all():
                print u'[%s] Consolidating legislator %s totals for legislature %d-%d…' % (
                    institution.siglum,
                    legislator.name,
                    legislature.date_start.year,
                    legislature.date_end.year
                )

                legislature_data = Expense.objects \
                    .filter(mandate__legislature=legislature) \
                    .filter(mandate__legislator=legislator) \
                    .values('mandate__legislator__id') \
                    .annotate(expensed=Sum('expensed')) \
                    .order_by('-expensed')

                if legislature_data:
                    legislature_data = legislature_data[0]
                else:
                    legislature_data = dict(expensed='0.')

                p = PerLegislator(
                    institution=institution,
                    legislature=legislature,
                    date_start=date_ranges['cdf'],
                    date_end=date_ranges['cdt'],
                    legislator=legislator,
                    expensed=legislature_data['expensed']
                )
                per_legislators_to_create.append(p)

            print u'[%s] Consolidating totals for legislator %s…' % (
                institution.siglum, legislator.name
            )

            p = PerLegislator(
                institution=institution,
                date_start=date_ranges['cdf'],
                date_end=date_ranges['cdt'],
                legislator=legislator,
                expensed=item['expensed']
            )
            per_legislators_to_create.append(p)
        PerLegislator.objects.bulk_create(per_legislators_to_create)

    def agnostic(self):
        # Institution-agnostic consolidations - biggest suppliers
        print u'Consolidating institution-agnostic totals…'

        BiggestSupplierForYear.objects.all().delete()

        years = [d.year for d in Expense.objects.dates('date', 'year')]
        for year in years:
            print u'Consolidating supplier totals for year %d…' % year
            data = Expense.objects \
                .filter(date__year=year) \
                .values('supplier__id') \
                .annotate(expensed=Sum('expensed')) \
                .order_by('-expensed')

            biggest_suppliers_for_year_to_add = list()
            for item in data:
                supplier = Supplier.objects.get(id=item['supplier__id'])

                b = BiggestSupplierForYear(
                    supplier=supplier,
                    year=year,
                    expensed=item['expensed']
                )
                biggest_suppliers_for_year_to_add.append(b)
            BiggestSupplierForYear.objects.bulk_create(biggest_suppliers_for_year_to_add)
