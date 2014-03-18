# -*- coding: utf-8 -*-
#
# Copyright (©) 2014 Gustavo Noronha Silva
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
from django.conf import settings
settings.DEBUG = False

from django.core.management.base import BaseCommand
from django.db.models import Sum
from montanha.models import Institution, Expense, ExpenseNature
from montanha.models import PerNature, PerNatureByYear
from montanha.util import filter_for_institution, get_date_ranges_from_data, ensure_years_in_range

debug_enabled = False


class Command(BaseCommand):
    args = "<source> [debug]"
    help = "Collects data for a number of sources"

    def debug(self, message):
        if debug_enabled:
            print message

    def handle(self, *args, **options):
        global debug_enabled

        if "debug" in args:
            debug_enabled = True

        institutions = []
        if "almg" in args:
            institutions.append(Institution.objects.get(siglum='ALMG'))

        if "senado" in args:
            institutions.append(Institution.objects.get(siglum='Senado'))

        if "cmbh" in args:
            institutions.append(Institution.objects.get(siglum='CMBH'))

        if "cmsp" in args:
            institutions.append(Institution.objects.get(siglum='CMSP'))

        if "camarafederal" in args:
            institutions.append(Institution.objects.get(siglum='CDF'))

        for institution in institutions:
            self.debug('Consolidating data for %s' % (institution.name))

            # Per nature
            PerNature.objects.filter(institution=institution).delete()
            PerNatureByYear.objects.filter(institution=institution).delete()

            data = Expense.objects.all()
            data = filter_for_institution(data, institution)

            date_ranges = get_date_ranges_from_data(institution, data)

            data = data.values('nature__id')
            data = data.annotate(expensed=Sum('expensed')).order_by('-expensed')

            years = [d.year for d in Expense.objects.dates('date', 'year')]
            years = ensure_years_in_range(date_ranges, years)

            per_natures_to_create = list()
            per_natures_by_year_to_create = list()
            for item in data:
                nature = ExpenseNature.objects.get(id=item['nature__id'])
                p = PerNature(institution=institution,
                              date_start=date_ranges['cdf'],
                              date_end=date_ranges['cdt'],
                              nature=nature,
                              expensed=item['expensed'])
                per_natures_to_create.append(p)

                for year in years:
                    year_data = Expense.objects.filter(nature=nature)
                    year_data = year_data.filter(date__year=year)
                    year_data = filter_for_institution(year_data, institution)
                    year_data = year_data.values('nature__id')
                    year_data = year_data.annotate(expensed=Sum("expensed"))

                    if year_data:
                        year_data = year_data[0]
                    else:
                        year_data = dict(expensed='0.')

                    p = PerNatureByYear(institution=institution,
                                        year=year,
                                        nature=nature,
                                        expensed=float(year_data['expensed']))
                    per_natures_by_year_to_create.append(p)
            PerNature.objects.bulk_create(per_natures_to_create)
            PerNatureByYear.objects.bulk_create(per_natures_by_year_to_create)
