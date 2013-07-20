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

import locale
from datetime import date
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.shortcuts import render
from django.db.models import Sum, Count
from montanha.models import *


locale.setlocale(locale.LC_MONETARY, "")


def show_index(request):

    c = {}

    return render(request, 'index.html', c)


def show_per_nature(request):

    data = Expense.objects.values('nature__name')
    data = data.annotate(expensed=Sum('expensed')).order_by('-expensed')

    years = [d.year for d in Expense.objects.dates('date', 'year')]

    # We use the data variable to get our list of expense natures so that we can
    # match the graph stacking with the order of the table rows
    time_series = []
    for nature_name in [d["nature__name"] for d in data]:
        nature = ExpenseNature.objects.get(name=nature_name)

        l = []
        cummulative = .0
        time_series.append(l)

        for year in years:
            year_data = Expense.objects.filter(nature=nature)
            year_data = year_data.filter(date__year=year)
            year_data = year_data.values("nature__name")
            year_data = year_data.annotate(expensed=Sum("expensed"))

            cummulative = cummulative + float(year_data[0]["expensed"])

            l.append([int(date(year, 1, 1).strftime("%s000")), cummulative])

    colors = ["#cb0d0d", "#cb410d", "#cbc40d", "#5fcb0d", "#0dcb14", "#0dcb68", "#0dcbc6", "#0d82cb",
              "#0d33cb", "#300dcb", "#7e0dcb", "#c80dcb", "#cb0d9a", "#cb0d3c", "#cb0d0d"]

    c = {'data': data, 'years_data': time_series, 'colors': colors}

    return render(request, 'per_nature.html', c)


def show_per_legislator(request):

    data = Expense.objects.values('mandate__legislator__name', 'mandate__party__siglum')
    data = data.annotate(expensed=Sum('expensed')).order_by('-expensed')

    c = {'data': data}

    return render(request, 'per_legislator.html', c)


def show_per_party(request):
    data = PoliticalParty.objects.raw("select montanha_politicalparty.id, "
                                      "siglum, count(distinct(montanha_legislator.id)) as n_legislators, "
                                      "sum(montanha_expense.expensed) as expensed_sum, "
                                      "sum(montanha_expense.expensed) / count(distinct(montanha_legislator.id)) as expensed_average "
                                      "from montanha_politicalparty, montanha_mandate, montanha_legislator, montanha_expense "
                                      "where montanha_politicalparty.id = montanha_mandate.party_id and "
                                      "montanha_mandate.legislator_id = montanha_legislator.id and "
                                      "montanha_expense.mandate_id = montanha_mandate.id "
                                      "group by siglum order by expensed_average desc")

    c = {'data': list(data)}

    return render(request, 'per_party.html', c)


def show_per_supplier(request):

    data = Expense.objects.values('supplier__name', 'supplier__identifier')
    data = data.annotate(expensed=Sum('expensed')).order_by('-expensed')

    paginator = Paginator(data, 10)
    page = request.GET.get('page')
    try:
        data = paginator.page(page)
    except PageNotAnInteger:
        data = paginator.page(1)
    except EmptyPage:
        data = paginator.page(paginator.num_pages)

    c = {'data': data}

    return render(request, 'per_supplier.html', c)
