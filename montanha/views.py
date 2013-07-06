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

from django.shortcuts import render
from django.db.models import Sum, Count
from montanha.models import *


def show_index(request):

    c = {}

    return render(request, 'index.html', c)


def show_per_nature(request):

    data = Expense.objects.values('nature__name')
    data = data.annotate(expensed=Sum('expensed')).order_by('-expensed')

    c = {'data': data}

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
