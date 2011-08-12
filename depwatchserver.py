#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (©) 2010 Gustavo Noronha Silva
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
import os
import os.path

import cherrypy
from cherrypy import tools
from sqlalchemy import func, desc, asc, or_
import json

from collector.models import Legislator, Expense, Supplier

import os.path
project_path = os.path.dirname(__file__)
if not project_path:
    project_path = os.getcwd()

from collector import models
Session = models.initialize('sqlite:///%s/data.db' % (project_path))


appdir = os.path.dirname(__file__)
if not appdir:
    appdir = '.'
appdir = os.path.abspath(appdir)


locale.setlocale(locale.LC_ALL, '')
locale.setlocale(locale.LC_MONETARY, 'pt_BR.UTF-8')


class DepWatchWeb(object):
    static = tools.staticdir.handler(section='static',
                                     root=appdir, dir='static')

    def index(self):
        raise cherrypy.HTTPRedirect('/static/index.html')
    index.exposed = True

    def _make_response(self, columns, data, graph_column = None, graph_title = '', show_graph = True):
        if graph_column is None:
            graph_column = len(columns) - 1

        last_line = [ 'Total' ]
        for column in columns[1:]:
            if column['type'] == 'money' or column['type'] == 'number':
                total = 0
                for expense in data:
                    total += expense[column['index']]
                last_line.append(total)
            else:
                last_line.append('')

        response = dict(graph_column = graph_column,
                        graph_title = graph_title,
                        show_graph = show_graph,
                        columns = columns,
                        data = data + [last_line])

        return unicode(json.dumps(response))

    def all(self, **kwargs):
        session = Session()

        start = int(kwargs['iDisplayStart'])
        end = start + int(kwargs['iDisplayLength'])
        sort_column = str(int(kwargs['iSortCol_0']) + 1) # sqlalchemy starts counting from 1

        if kwargs['sSortDir_0'] == 'asc':
            sort_order = asc
        else:
            sort_order = desc

        expenses_query = session.query(Expense.nature, Legislator.name, Legislator.party,
                                       Supplier.name, Supplier.cnpj, Expense.number,
                                       Expense.date, Expense.expensed
                                       ).join('legislator').join('supplier').order_by(sort_order(sort_column))

        total_results = expenses_query.count()

        search_string = kwargs['sSearch'].decode('utf-8')
        if search_string:
            expenses_query = expenses_query.filter(or_(Expense.nature.like('%' + search_string + '%'),
                                                       Legislator.name.like('%' + search_string + '%'),
                                                       Legislator.party.like('%' + search_string + '%'),
                                                       Supplier.name.like('%' + search_string + '%'),
                                                       Supplier.cnpj.like('%' + search_string + '%')))
        display_results = expenses_query.count()
        expenses = expenses_query[start:end]

        # Format money and date columns.
        data = []
        for item in expenses:
            item = list(item)
            item[-2] = item[-2].strftime('%d/%m/%Y')
            item[-1] = locale.currency(float(item[-1]), grouping = True)
            data.append(item)

        response = dict(sEcho = int(kwargs['sEcho']),
                        iTotalRecords = total_results,
                        iTotalDisplayRecords = display_results,
                        aaData = data)
        return unicode(json.dumps(response))
    all.exposed = True

    def legislator_all(self, legislator_id, **kwargs):
        session = Session()

        start = int(kwargs['iDisplayStart'])
        end = start + int(kwargs['iDisplayLength'])
        sort_column = str(int(kwargs['iSortCol_0']) + 1) # sqlalchemy starts counting from 1

        if kwargs['sSortDir_0'] == 'asc':
            sort_order = asc
        else:
            sort_order = desc

        legislator = session.query(Legislator).get(legislator_id)
        expenses_query = session.query(Expense.nature, Supplier.name, Supplier.cnpj,
                                       Expense.number, Expense.date, Expense.expensed
                                       ).join('supplier').order_by(sort_order(sort_column))

        expenses_query = expenses_query.filter(Expense.legislator == legislator)

        total_results = expenses_query.count()

        search_string = kwargs['sSearch'].decode('utf-8')
        if search_string:
            expenses_query = expenses_query.filter(or_(Expense.nature.like('%' + search_string + '%'),
                                                       Supplier.name.like('%' + search_string + '%'),
                                                       Supplier.cnpj.like('%' + search_string + '%')))
        display_results = expenses_query.count()
        expenses = expenses_query[start:end]

        # Format money and date columns.
        data = []
        for item in expenses:
            item = list(item)
            item[-2] = item[-2].strftime('%d/%m/%Y')
            item[-1] = locale.currency(float(item[-1]), grouping = True)
            data.append(item)

        response = dict(sEcho = int(kwargs['sEcho']),
                        iTotalRecords = total_results,
                        iTotalDisplayRecords = display_results,
                        aaData = data)
        return unicode(json.dumps(response))
    legislator_all.exposed = True

    def per_legislator(self):
        session = Session()

        expenses = session.query(Legislator.id, Legislator.name, Legislator.party,
                                 func.sum(Expense.expensed)).join('expenses').group_by(Legislator.party, Legislator.name).order_by(desc('3')).all()

        data = []
        for exp in expenses:
            line = []
            line.append('<a href="javascript:detail_legislator(%d, \'%s\', \'%s\')">%s</a>' % (exp[0], exp[1], exp[2], exp[1]))
            line += exp[2:]
            data.append(line)

        columns = []
        columns.append(dict(label = u'Deputad@', type = 'string', index = 0))
        columns.append(dict(label = u'Partido', type = 'string', index = 1))
        columns.append(dict(label = u'Valor ressarcido', type = 'money', index = 2))
        return self._make_response(columns, data, show_graph = False)
    per_legislator.exposed = True

    def per_party(self):
        session = Session()

        expenses = session.query(Legislator.party, func.count(func.distinct(Legislator.name)),
                                 func.sum(Expense.expensed)).join('expenses').group_by(Legislator.party).all()

        expenses = [[party, num_legislators, expensed, expensed / num_legislators]
                     for party, num_legislators, expensed in expenses]

        # Order by expense per legislator.
        expenses.sort(cmp = lambda x, y: cmp(y[3], x[3]))

        columns = []
        columns.append(dict(label = u'Partido', type = 'string', index = 0))
        columns.append(dict(label = u'Deputad@s', type = 'number', index = 1))
        columns.append(dict(label = u'Valor ressarcido', type = 'money', index = 2))
        columns.append(dict(label = u'Média', type = 'money', index = 3, skip_total = True))

        graph_title = u'Gasto médio por partido'
        return self._make_response(columns, expenses, graph_title = graph_title)
    per_party.exposed = True

    def per_supplier(self):
        session = Session()

        expenses = session.query(Supplier.name, Supplier.cnpj,
                                 func.sum(Expense.expensed)).join('expenses').group_by(Supplier.cnpj).order_by(desc('3')).all()

        columns = []
        columns.append(dict(label = u'Empresa/Pessoa', type = 'string', index = 0))
        columns.append(dict(label = u'CNPJ/CPF', type = 'string', index = 1))
        columns.append(dict(label = u'Valor recebido', type = 'money', index = 2))
        return self._make_response(columns, expenses, show_graph = False)
    per_supplier.exposed = True

    def per_nature(self):
        session = Session()

        expenses = session.query(Expense.nature,
                                 func.sum(Expense.expensed)).group_by(Expense.nature).all()

        columns = []
        columns.append(dict(label = u'Tipo de gasto', type = 'string', index = 0))
        columns.append(dict(label = u'Valor ressarcido', type = 'money', index = 1))

        graph_title = u'Total de gasto por tipo'
        return self._make_response(columns, expenses, graph_title = graph_title)
    per_nature.exposed = True


def setup_server():
    cherrypy.config.update({'environment': 'production',
                            'log.screen': False,
                            'show_tracebacks': True})
    cherrypy.tree.mount(DepWatchWeb())

if __name__ == '__main__':
    cherrypy.quickstart(DepWatchWeb())
