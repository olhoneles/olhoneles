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
import json
from colorsys import hsv_to_rgb
from datetime import date
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.shortcuts import render as original_render
from django.db.models import Sum, Count, Q
from django.http import HttpResponse
from django.core.cache import cache
from django.core.mail import send_mail
from django.conf import settings
from montanha.models import *
from montanha.forms import *
from montanha.util import filter_for_institution, get_date_ranges_from_data

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


def show_index(request, institution):

    c = {}

    if institution:
        c['img'] = institution.lower() + '.png'
        return new_render(request, institution, 'institution.html', c)

    return new_render(request, institution, 'index.html', c)


def show_robots_txt(request):
    return HttpResponse('User-Agent: *\nAllow: /\n')


def error_500(request):
    c = {}
    return original_render(request, '500.html', c)


def error_404(request):
    c = {}
    return original_render(request, '404.html', c)


def show_per_nature(request, institution):

    institution = Institution.objects.get(siglum=institution)
    data = PerNature.objects.filter(institution=institution)

    date_ranges = get_date_ranges_from_data(institution, data, consolidated_data=True)

    time_series = []
    for d in data:
        l = []
        cummulative = .0
        time_series.append(dict(label=d.nature.name, data=l))

        for item in PerNatureByYear.objects.filter(institution=institution).filter(nature=d.nature):
            cummulative = cummulative + float(item.expensed)
            l.append([int(date(item.year, 1, 1).strftime("%s000")), cummulative])

    # mbm_years = list of years (3, right now - 2011, 2012, 2013) with 12 months inside
    # each month in turn carries a dict with month name and value or null.
    def nature_is_empty(years):
        for year in years:
            for month in year['data']:
                if month['data'] != 'null' and month['data'] > 0.0001:
                    return False
        return True

    natures_mbm = []
    for nature in ExpenseNature.objects.all():
        mbm_years = []
        expensed_by_month = PerNatureByMonth.objects.filter(institution=institution)
        expensed_by_month = expensed_by_month.filter(nature=nature)
        all_years = [d.year for d in expensed_by_month.dates('date', 'year')]
        for year in all_years:
            mbm_series = []
            for month in range(1, 13):
                month_date = date(year, month, 1)

                mname = month_date.strftime("%b")
                try:
                    item = expensed_by_month.get(date=month_date)
                    expensed = float(item.expensed)
                except PerNatureByMonth.DoesNotExist:
                    expensed = 'null'

                mbm_series.append(dict(month=mname, data=str(expensed)))
            mbm_years.append(dict(label=year, data=mbm_series))

        if not nature_is_empty(mbm_years):
            natures_mbm.append(dict(name=nature.name, data=mbm_years))

    c = {'data': data, 'years_data': time_series, 'natures_mbm': natures_mbm,
         'colors': generate_colors(len(data), 0.93, 0.8)}

    c.update(date_ranges)

    return new_render(request, institution.siglum, 'per_nature.html', c)


def show_per_legislator(request, institution):

    data = Expense.objects.all()
    data = filter_for_institution(data, institution)

    date_ranges = get_date_ranges_from_data(institution, data)

    data = data.values('mandate__legislator__id',
                       'mandate__legislator__name',
                       'mandate__date_start',
                       'mandate__date_end',
                       'mandate__party__siglum',
                       'mandate__party__name',
                       'mandate__party__logo')
    data = data.annotate(expensed=Sum('expensed'))

    # We may have several mandates for a legislator, potentially with different parties.
    # We only want to show one line per legislator, though, so sum the expenses and list
    # all parties in the party column.
    data_dict = {}
    data_list = []
    for d in data:
        key = d['mandate__legislator__id']
        party = {'siglum': d['mandate__party__siglum'],
                 'name': d['mandate__party__name'],
                 'logo': d['mandate__party__logo'],
                 'year': d['mandate__date_start'].year,
                 'year_end': ''}
        if d['mandate__date_end']:
            party['year_end'] = d['mandate__date_end'].year

        if key in data_dict:
            data_dict[key]['expensed'] + d['expensed']
            data_dict[key]['parties'].append(party)
            data_dict[key]['parties'].sort(key=lambda p: p['year'])
        else:
            data_dict[key] = d
            data_dict[key]['parties'] = [party]
            data_list.append(d)

    data = data_list
    data.sort(key=lambda d: d['expensed'], reverse=True)

    c = {'data': data}

    c.update(date_ranges)

    return new_render(request, institution, 'per_legislator.html', c)


def show_legislator_detail(request, institution, legislator_id):

    data = Expense.objects.all()

    if institution:
        data = filter_for_institution(data, institution)

    date_ranges = get_date_ranges_from_data(institution, data)

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

    c.update(date_ranges)

    return new_render(request, institution, 'detail_legislator.html', c)


def postprocess_party_data(institution, data):
    if institution:
        institution = Institution.objects.get(siglum=institution)
    for d in list(data):
        if d['mandate__party__siglum']:
            party = PoliticalParty.objects.get(siglum=d['mandate__party__siglum'])
            if institution:
                mandates = party.mandate_set.filter(legislature__institution=institution)
            d['n_legislators'] = mandates.values('legislator').count()
            d['expensed_average'] = d['expensed'] / d['n_legislators']
        else:
            d['mandate__party__siglum'] = 'NC'
            d['mandate__party__name'] = 'Desconhecido'
            mandates = Mandate.objects.filter(party__siglum=None)
            if institution:
                mandates = mandates.filter(legislature__institution=institution)
            d['n_legislators'] = mandates.values('legislator').count()
            d['expensed_average'] = d['expensed'] / d['n_legislators']

    return sorted(data, key=lambda d: d['expensed_average'], reverse=True)


def show_per_party(request, institution):

    data = Expense.objects.all()
    data = filter_for_institution(data, institution)

    date_ranges = get_date_ranges_from_data(institution, data)

    data = data.values('mandate__party__logo', 'mandate__party__siglum', 'mandate__party__name')
    data = data.annotate(expensed=Sum('expensed'))

    data = postprocess_party_data(institution, data)

    c = {'data': data, 'graph_data': data, 'colors': generate_colors(len(data), 0.93, 0.8)}

    c.update(date_ranges)

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

    date_ranges = get_date_ranges_from_data(institution, data)

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

    c.update(date_ranges)

    return new_render(request, institution, 'per_supplier.html', c)


def show_supplier_detail(request, institution, supplier_id):

    data = Expense.objects.all()
    data = filter_for_institution(data, institution)

    date_ranges = get_date_ranges_from_data(institution, data)

    supplier = Supplier.objects.get(pk=supplier_id)
    data = data.filter(supplier=supplier)

    # Data prepared for displaying the per-party graph
    graph_data = data.values('mandate__party__logo', 'mandate__party__siglum', 'mandate__party__name')
    graph_data = graph_data.annotate(expensed=Sum('expensed'))
    graph_data = postprocess_party_data(institution, graph_data)

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

    c.update(date_ranges)

    return new_render(request, institution, 'detail_supplier.html', c)


def deep_getattr(obj, attr):
    return reduce(getattr, attr.split('.'), obj)


def convert_data_to_list(data, columns):
    data_list = []
    for item in data:
        sublist = []
        for field, field_type in columns:
            value = deep_getattr(item, field)

            if field_type == 'm':
                value = locale.currency(value, grouping=True).replace(" ", "&nbsp;")

            if isinstance(value, date):
                value = value.strftime('%d/%m/%Y')

            sublist.append(value)
        data_list.append(sublist)
    return data_list


def cleanup_date_ranges(date_ranges):
    del date_ranges['cdf']
    del date_ranges['cdt']


def data_tables_query(request, institution, columns, filter_function=None):

    data = Expense.objects.all()
    data = filter_for_institution(data, institution)

    if filter_function:
        data = filter_function(data)

    date_ranges = get_date_ranges_from_data(institution, data, False)

    total_results = data.count()

    search_string = request.GET.get('sSearch').decode('utf-8')
    if search_string:
        def format_for_column_type(col_type, search_string):
            if col_type == 'm':
                search_string = search_string.replace('.', '').replace(',', '.')
                search_string = search_string.replace('R$', '')
                return search_string.strip()
            return search_string

        filter_expression = None
        for name, col_type in columns:
            actual_search_string = format_for_column_type(col_type, search_string)
            exp = Q(**{name.replace('.', '__') + '__icontains': actual_search_string})
            if filter_expression:
                filter_expression |= exp
            else:
                filter_expression = exp
        data = data.filter(filter_expression)

    displayed_results = data.count()

    # Sort by expense by default, assumed to be the last column.
    sort_col = int(request.GET.get('iSortCol_0', len(columns) - 1))
    order_by_field = columns[sort_col][0].replace('.', '__')

    sort_direction = request.GET.get('sSortDir_0', 'asc')
    if sort_direction == 'desc':
        order_by_field = '-' + order_by_field

    data = data.order_by(order_by_field)

    per_page = int(request.GET.get('iDisplayLength', 10))
    starting_at = int(request.GET.get('iDisplayStart', 0))
    page = starting_at > 0 and starting_at / per_page + 1 or 1

    paginator = Paginator(data, per_page)
    try:
        data = paginator.page(page)
    except PageNotAnInteger:
        data = paginator.page(1)
    except EmptyPage:
        data = paginator.page(paginator.num_pages)

    data = convert_data_to_list(data, columns)

    response = dict(sEcho=int(request.GET.get('sEcho', 0)),
                    iTotalRecords=total_results,
                    iTotalDisplayRecords=displayed_results,
                    aaData=data)

    response.update(date_ranges)

    return HttpResponse(json.dumps(response), content_type='application/json')


def query_all(request, institution):
    columns = (
        ('nature.name', 's'),
        ('mandate.legislator.name', 's'),
        ('supplier.name', 's'),
        ('supplier.identifier', 's'),
        ('number', 's'),
        ('date', 'd'),
        ('expensed', 'm'),
    )

    return data_tables_query(request, institution, columns)


def query_supplier_all(request, institution):
    def filter_function(data):
        supplier = Supplier.objects.get(id=request.GET['item_id'])
        return data.filter(supplier=supplier)

    columns = (
        ('nature.name', 's'),
        ('mandate.legislator.name', 's'),
        ('number', 's'),
        ('date', 'd'),
        ('expensed', 'm'),
    )

    return data_tables_query(request, institution, columns, filter_function)


def query_legislator_all(request, institution):
    def filter_function(data):
        legislator = Legislator.objects.get(id=request.GET['item_id'])
        return data.filter(mandate__legislator=legislator)

    columns = (
        ('nature.name', 's'),
        ('supplier.name', 's'),
        ('supplier.identifier', 's'),
        ('number', 's'),
        ('date', 'd'),
        ('expensed', 'm'),
    )

    return data_tables_query(request, institution, columns, filter_function)


def show_all(request, institution):

    c = {}

    data = Expense.objects.all()

    if institution:
        data = filter_for_institution(data, institution)

    date_ranges = get_date_ranges_from_data(institution, data)
    c.update(date_ranges)

    return new_render(request, institution, 'all_expenses.html', c)


def what_is_expenses(request):

    c = {}

    return original_render(request, 'what_is_expenses.html', c)


def contact_us(request):

    contact_us_form = ContactUsForm(request.POST or None)
    success_message = ''

    if request.POST and contact_us_form.is_valid():
        subject = '[Olho Neles]: Fale Conosco'

        message = ('Nome: %s\nEmail: %s\nIP: %s\nMensagem:\n\n%s') % (
            contact_us_form.cleaned_data['name'],
            contact_us_form.cleaned_data['email'],
            request.META['REMOTE_ADDR'],
            contact_us_form.cleaned_data['message'])

        from_field = '%s <%s>' % (contact_us_form.cleaned_data['name'],
                                  contact_us_form.cleaned_data['email'])

        send_mail(subject, message, from_field, [settings.CONTACT_US_EMAIL])

        success_message = ("""Sua mensagem foi enviada com sucesso. """
                           """Em breve entraremos em contato!""")

        contact_us_form = ContactUsForm(None)

    c = {'contact_us_form': contact_us_form,
         'success_message': success_message}

    return original_render(request, 'contact_us.html', c)
