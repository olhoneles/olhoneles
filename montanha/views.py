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
import pickle
from colorsys import hsv_to_rgb
from datetime import date
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.shortcuts import render as original_render
from django.db.models import Sum, Count
from django.core.cache import cache
from django.core.mail import send_mail
from django.conf import settings
from montanha.models import *
from montanha.forms import *

locale.setlocale(locale.LC_MONETARY, "pt_BR.UTF-8")
locale.setlocale(locale.LC_TIME, "pt_BR.UTF-8")


def generate_colors(n=7, sat=1.0, val=1.0):
    '''Generates an array of n colors from red to violet, considering
    saturation sat and value val'''
    return ['#%02X%02X%02X' % t for t in [tuple([int(round(c * 255)) for c in t]) for t in
           [hsv_to_rgb(x/float(n), sat, val) for x in xrange(0, n)]]]


def render(request, to_disable, template, context):
    disable_list = to_disable and [item for item in to_disable[3:].split(',')] or []

    institutions = Institution.objects.all()
    institution_dicts = []
    for institution in institutions:
        d = {}
        d["siglum"] = institution.siglum
        d["name"] = institution.name
        d["logo"] = institution.logo
        d["enabled"] = institution.siglum not in disable_list
        legislatures = institution.legislature_set.all()
        if legislatures.count() > 1:
            legislature_dicts = []
            for legislature in legislatures:
                l = {}
                l["date_start"] = legislature.date_start
                l["date_end"] = legislature.date_end
                legislature_string = '%s-%d' % (institution.siglum, legislature.date_start.year)
                l["enabled"] = legislature_string in disable_list
                legislature_dicts.append(l)
            d["legislatures"] = legislature_dicts
        else:
            d["legislatures"] = None
        institution_dicts.append(d)
    context['institutions'] = institution_dicts
    context['extra_uri'] = to_disable

    # This is just to simplify the conversion to the single-institution-or-all view model,
    # so that we can reuse templates between both code paths for a while.
    context['institution'] = None

    return original_render(request, template, context)


def new_render(request, institution, template, context):
    context['institution'] = None
    if institution:
        context['institution'] = Institution.objects.get(siglum=institution)
    return original_render(request, template, context)


def exclude_disabled(data, to_disable):
    if not to_disable:
        return data

    for item in to_disable[3:].split(','):
        parts = item.split('-')

        if len(parts) == 1:
            institution = Institution.objects.get(siglum=parts[0])
            data = data.exclude(mandate__legislature__institution=institution)
        elif len(parts) == 2:
            institution = Institution.objects.get(siglum=parts[0])
            legislature = institution.legislature_set.get(date_start__year=parts[1])
            data = data.exclude(mandate__legislature=legislature)

    return data


def filter_for_institution(data, institution):
    if not institution:
        return data

    institution = Institution.objects.get(siglum=institution)
    data = data.filter(mandate__legislature__institution=institution)
    return data


def show_index(request, institution):

    c = {}

    return new_render(request, institution, 'index.html', c)


def error_500(request):
    c = {}
    return original_render(request, '500.html', c)


def error_404(request):
    c = {}
    return original_render(request, '404.html', c)


def show_per_nature(request, institution):

    data = Expense.objects.all()
    data = filter_for_institution(data, institution)

    data = data.values('nature__name')
    data = data.annotate(expensed=Sum('expensed')).order_by('-expensed')

    years = [d.year for d in Expense.objects.dates('date', 'year')]

    # We use the data variable to get our list of expense natures so that we can
    # match the graph stacking with the order of the table rows, it also makes
    # it easier to filter for the institution.
    time_series = []
    for nature_name in [d["nature__name"] for d in data]:
        nature = ExpenseNature.objects.get(name=nature_name)

        l = []
        cummulative = .0
        time_series.append(dict(label=nature_name, data=l))

        for year in years:
            year_data = Expense.objects.filter(nature=nature)
            year_data = year_data.filter(date__year=year)
            year_data = year_data.values("nature__name")
            year_data = year_data.annotate(expensed=Sum("expensed"))

            if year_data:
                cummulative = cummulative + float(year_data[0]["expensed"])

            l.append([int(date(year, 1, 1).strftime("%s000")), cummulative])

    # mbm_years = list of years (3, right now - 2011, 2012, 2013) with 12 months inside
    # each month in turn carries a dict with month name and value or null.
    def nature_is_empty(years):
        for year in years:
            for month in year['data']:
                if month['data'] != 'null' and month['data'] > 0.0001:
                    return False
        return True

    natures_mbm = cache.get(request.get_full_path() + '-natures_mbm')
    if natures_mbm:
        natures_mbm = pickle.loads(natures_mbm)
    else:
        natures_mbm = []
        for nature in ExpenseNature.objects.all():
            mbm_years = []
            last_year = 2013
            for year in [2011, 2012, 2013]:
                mbm_series = []

                expenses = Expense.objects.filter(nature=nature).filter(date__year=year)
                expenses = filter_for_institution(expenses, institution)
                last_month = expenses and expenses.order_by('-date')[0].date.month or 0

                for month in range(1, 13):
                    mname = date(year, month, 1).strftime("%b")
                    mdata = expenses.filter(date__month=month)
                    mdata = mdata.values('nature__name')
                    mdata = mdata.annotate(expensed=Sum('expensed')).order_by('-expensed')

                    if mdata:
                        mdata = mdata[0]['expensed']
                    else:
                        # If we reached the last month we have any data for, use null instead of
                        # 0., so the graph gets cut out.
                        if last_year and month > last_month:
                            mdata = 'null'
                        else:
                            mdata = 0.

                    mbm_series.append(dict(month=mname, data=mdata))

                mbm_years.append(dict(label=year, data=mbm_series))

            if not nature_is_empty(mbm_years):
                natures_mbm.append(dict(name=nature.name, data=mbm_years))

        cache.set(request.get_full_path() + '-natures_mbm', pickle.dumps(natures_mbm), 36288000)

    c = {'data': data, 'years_data': time_series, 'natures_mbm': natures_mbm, 'colors': generate_colors(len(data), 0.93, 0.8)}

    return new_render(request, institution, 'per_nature.html', c)


def show_per_legislator(request, institution):

    data = Expense.objects.all()
    data = filter_for_institution(data, institution)

    data = data.values('mandate__legislator__id',
                       'mandate__legislator__name',
                       'mandate__party__siglum',
                       'mandate__party__name',
                       'mandate__party__logo')
    data = data.annotate(expensed=Sum('expensed')).order_by('-expensed')

    c = {'data': data}

    return new_render(request, institution, 'per_legislator.html', c)


def show_legislator_detail(request, institution, legislator_id):

    data = Expense.objects.all()
    data = filter_for_institution(data, institution)

    legislator = Legislator.objects.get(pk=legislator_id)
    data = data.filter(mandate__legislator=legislator)

    top_suppliers = data.values('supplier__id',
                                'supplier__identifier',
                                'supplier__name')
    top_suppliers = top_suppliers.annotate(expensed=Sum('expensed')).order_by('-expensed')
    top_suppliers = top_suppliers[:15]

    total_expensed = data.values('supplier__name')
    total_expensed = total_expensed.annotate(total_expensed=Sum('expensed'))[0]['total_expensed']

    data = data.values('nature__name', 'supplier__name', 'supplier__identifier',
                       'number', 'date', 'expensed').order_by('-date')

    paginator = Paginator(data, 10)
    page = request.GET.get('page')
    try:
        data = paginator.page(page)
    except PageNotAnInteger:
        data = paginator.page(1)
    except EmptyPage:
        data = paginator.page(paginator.num_pages)

    c = {'legislator': legislator, 'data': data, 'top_suppliers': top_suppliers}

    return new_render(request, institution, 'detail_legislator.html', c)


def postprocess_party_data(data):
    for d in list(data):
        if d['mandate__party__siglum']:
            party = PoliticalParty.objects.get(siglum=d['mandate__party__siglum'])
            d['n_legislators'] = party.mandate_set.values('legislator').count()
            d['expensed_average'] = d['expensed'] / d['n_legislators']
        else:
            d['mandate__party__siglum'] = 'NC'
            d['mandate__party__name'] = 'Desconhecido'
            d['n_legislators'] = Legislator.objects.filter(mandate__party__siglum=None).count()
            d['expensed_average'] = d['expensed'] / d['n_legislators']

    return sorted(data, key=lambda d: d['expensed_average'], reverse=True)


def show_per_party(request, institution):

    data = Expense.objects.all()
    data = filter_for_institution(data, institution)

    data = data.values('mandate__party__logo', 'mandate__party__siglum', 'mandate__party__name')
    data = data.annotate(expensed=Sum('expensed'))

    data = postprocess_party_data(data)

    c = {'data': data, 'graph_data': data, 'colors': generate_colors(len(data), 0.93, 0.8)}

    return new_render(request, institution, 'per_party.html', c)


def add_sorting(request, data, default='-expensed'):
    if 'order_by' in request.GET:
        order_by_field = request.GET.get('order_by')
        if not 'asc' in request.GET or not request.GET.get('asc'):
            order_by_field = '-' + order_by_field
        data = data.order_by(order_by_field)
    else:
        data = data.order_by(default)
    return data


def show_per_supplier(request, institution):

    data = Expense.objects.all()
    data = filter_for_institution(data, institution)

    data = data.values('supplier__id', 'supplier__name', 'supplier__identifier')
    data = data.annotate(expensed=Sum('expensed'))

    data = add_sorting(request, data)

    paginator = Paginator(data, 10)
    page = request.GET.get('page')
    try:
        data = paginator.page(page)
    except PageNotAnInteger:
        data = paginator.page(1)
    except EmptyPage:
        data = paginator.page(paginator.num_pages)

    c = {'data': data}

    return new_render(request, institution, 'per_supplier.html', c)


def show_supplier_detail(request, institution, supplier_id):

    data = Expense.objects.all()
    data = filter_for_institution(data, institution)

    supplier = Supplier.objects.get(pk=supplier_id)
    data = data.filter(supplier=supplier)

    # Data prepared for displaying the per-party graph
    graph_data = data.values('mandate__party__logo', 'mandate__party__siglum', 'mandate__party__name')
    graph_data = graph_data.annotate(expensed=Sum('expensed'))
    graph_data = postprocess_party_data(graph_data)

    top_buyers = data.values('mandate__legislator__id',
                             'mandate__legislator__name',
                             'mandate__party__siglum')
    top_buyers = top_buyers.annotate(expensed=Sum('expensed')).order_by('-expensed')
    top_buyers = top_buyers[:15]

    total_expensed = data.values('supplier__name')
    total_expensed = total_expensed.annotate(total_expensed=Sum('expensed'))[0]['total_expensed']

    data = data.values('nature__name',
                       'mandate__legislator__name', 'mandate__party__siglum',
                       'number', 'date', 'expensed').order_by('-date')

    paginator = Paginator(data, 10)
    page = request.GET.get('page')
    try:
        data = paginator.page(page)
    except PageNotAnInteger:
        data = paginator.page(1)
    except EmptyPage:
        data = paginator.page(paginator.num_pages)

    c = {'supplier': supplier,
         'data': data,
         'graph_data': graph_data,
         'top_buyers': top_buyers,
         'total_expensed': total_expensed,
         'colors': generate_colors(len(data), 0.93, 0.8)}

    return new_render(request, institution, 'detail_supplier.html', c)


def show_all(request, institution):

    data = Expense.objects.all()
    data = filter_for_institution(data, institution)

    data = add_sorting(request, data, '-date')

    paginator = Paginator(data, 10)
    page = request.GET.get('page')
    try:
        data = paginator.page(page)
    except PageNotAnInteger:
        data = paginator.page(1)
    except EmptyPage:
        data = paginator.page(paginator.num_pages)

    c = {'data': data}

    return new_render(request, institution, 'all_expenses.html', c)


def what_is_expenses(request, institution):

    c = {}

    return new_render(request, institution, 'what_is_expenses.html', c)


def contact_us(request, institution):

    contact_us_form = ContactUsForm(request.POST or None)
    success_message = ''

    if request.POST and contact_us_form.is_valid():
        subject = '[Montanha Site]: Fale Conosco'

        message = ('Nome: %s\nEmail: %s\nIP: %s\nMensagem:\n\n%s') % (
            contact_us_form.cleaned_data['name'],
            contact_us_form.cleaned_data['email'],
            request.META['REMOTE_ADDR'],
            contact_us_form.cleaned_data['message'])

        from_field = '%s <%s>' % (contact_us_form.cleaned_data['name'],
                                  contact_us_form.cleaned_data['email'])

        send_mail(subject, message, from_field, [settings.DEFAULT_FROM_EMAIL])

        success_message = ("""Sua mensagem foi enviada com sucesso. """
                           """Em breve entraremos em contato!""")

        contact_us_form = ContactUsForm(None)

    c = {'contact_us_form': contact_us_form,
         'success_message': success_message}

    return new_render(request, institution, 'contact_us.html', c)
