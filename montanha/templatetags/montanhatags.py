# -*- coding: utf-8 -*-
#
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

from django import template
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe

from montanha.cpf import Cpf
from montanha.cnpj import Cnpj


register = template.Library()


@register.filter
def format_currency(value):
    if value:
        return mark_safe(locale.currency(value, grouping=True).replace(" ", "&nbsp;"))
    else:
        return ''


@register.filter
def itercycle(iterable, counter):
    return iterable[counter % len(iterable)]


@register.simple_tag(takes_context=True)
def sortable_th(context, tag_id, is_default=False):
    request = context["request"]

    th_attr = 'id="%s"' % tag_id
    if request.GET.get("order_by") == tag_id or (is_default and "order_by" not in request.GET):
        th_attr += ' class="sortable'
        if request.GET.get("asc"):
            th_attr += ' sorted-asc'
        else:
            th_attr += ' sorted'
        th_attr += '"'

    return mark_safe(th_attr)


@register.simple_tag
def expenses_table(*args):
    return render_to_string('expenses_table.html', dict(columns=args))


@register.simple_tag(takes_context=True)
def expenses_data_table(context, query_name, col_types, item_id=None):
    columns = []
    for c in col_types:
        if c == 'm':
            columns.append("{ sType: 'money' }")
        else:
            columns.append('null')
    c = dict(institution=context['institution'],
             legislature=context['legislature'],
             filter_spec=context['filter_spec'],
             item_id=item_id,
             query_name=query_name, columns=columns)
    return render_to_string('expenses_data_table.html', c)


@register.simple_tag
def biggest_suppliers_table(*args):
    return render_to_string('biggest_suppliers_table.html', dict(columns=args))


@register.simple_tag(takes_context=True)
def biggest_suppliers_data_table(context, query_name, col_types, item_id=None):
    columns = []
    for c in col_types:
        if c == 'm':
            columns.append("{ sType: 'money' }")
        else:
            columns.append('null')
    c = dict(institution=context['institution'],
             legislature=context['legislature'],
             filter_spec=context['filter_spec'],
             item_id=item_id,
             query_name=query_name, columns=columns)
    return render_to_string('biggest_suppliers_data_table.html', c)


# FIXME: duplicated code
@register.filter
def supplier_with_mask(value):
    try:
        if len(value) == 11:
            return mark_safe(Cpf().format(value))
        elif len(value) == 14:
            return mark_safe(Cnpj().format(value))
        else:
            return value
    except:
        return value
