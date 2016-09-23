# -*- coding: utf-8 -*-
#
# Copyright (©) 2013 Marcelo Jorge Vieira <metal@alucinados.com>
# Copyright (©) 2013 Gustavo Noronha Silva <gustavo@noronha.eti.br>
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

from datetime import date

from montanha.models import Institution, Legislature


def filter_for_institution(data, institution):
    if not institution:
        return data

    if not isinstance(institution, Institution):
        institution = Institution.objects.get(siglum=institution)

    data = data.filter(mandate__legislature__institution=institution)
    return data


def get_date_ranges_from_data(institution, data, consolidated_data=False, include_date_objects=True):
    """ Takes a data set and returns a dict containing in textual form:

        current_date_from: the start date that is being used for this query
        current_date_to: the end date that is being used for this query
    """
    try:
        if consolidated_data:
            cdf = data.order_by('date_start')[0].date_start
        else:
            cdf = data.order_by('date')[0].date
    except:
        cdf = date.today()

    try:
        if consolidated_data:
            cdt = data.order_by('-date_end')[0].date_end
        else:
            cdt = data.order_by('-date')[0].date
    except:
        cdt = date.today()

    if institution:
        if not isinstance(institution, Institution):
            institution = Institution.objects.get(siglum=institution)

        # Bound dates to the start of the first legislature to the end
        # of the last, which makes more sense to our purposes.
        first = institution.legislature_set.order_by('date_start')[0]
        last = institution.legislature_set.order_by('-date_end')[0]
    else:
        first = Legislature.objects.order_by('date_start')[0]
        last = Legislature.objects.order_by('-date_end')[0]

    min_date = first.date_start
    max_date = last.date_end

    if cdf < min_date:
        cdf = min_date

    if cdt > max_date:
        cdt = max_date

    cdf_string = cdf.strftime('%B de %Y')
    cdt_string = cdt.strftime('%B de %Y')

    d = dict(current_date_from=cdf_string, current_date_to=cdt_string)
    if include_date_objects:
        d.update(dict(cdf=cdf, cdt=cdt))

    return d


def ensure_years_in_range(date_ranges, years):
    nyears = []
    cdf = date_ranges['cdf']
    cdt = date_ranges['cdt']
    for y in years:
        d = date(y, 1, 1)
        if d < cdf or d > cdt:
            continue
        nyears.append(y)
    return nyears
