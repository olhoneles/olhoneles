#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (©) 2010, 2011, 2012 Gustavo Noronha Silva
# Copyright (©) 2010, 2011 Estêvão Samuel Procópio
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

project_path = os.path.dirname(__file__)
if not project_path:
    project_path = os.getcwd()
project_path = os.path.abspath(os.path.join(project_path, '..'))

appdir = os.path.dirname(__file__)
if not appdir:
    appdir = ''
appdir = os.path.abspath(os.path.join(appdir, '..'))


locale.setlocale(locale.LC_ALL, '')
locale.setlocale(locale.LC_MONETARY, 'pt_BR.UTF-8')


cherrypy.engine.autoreload.files.add(appdir + '/templates/index.html')


html_data = open(appdir + '/templates/index.html').read()


class QueryServer(object):
    def __init__(self, config, models):
        self.Session = models.initialize('sqlite:///%s/%s/data.db' % (project_path, config['base_path']))
        self.Legislator = models.Legislator
        self.Expense = models.Expense
        self.Supplier = models.Supplier


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
        session = self.Session()

        start = int(kwargs['iDisplayStart'])
        end = start + int(kwargs['iDisplayLength'])
        sort_column = str(int(kwargs['iSortCol_0']) + 1) # sqlalchemy starts counting from 1

        if kwargs['sSortDir_0'] == 'asc':
            sort_order = asc
        else:
            sort_order = desc

        expenses_query = session.query(self.Expense.nature, self.Legislator.name, self.Legislator.party,
                                       self.Supplier.name, self.Supplier.cnpj, self.Expense.number,
                                       self.Expense.date, self.Expense.expensed
                                       ).join('legislator').join('supplier').order_by(sort_order(sort_column))

        total_results = expenses_query.count()

        search_string = kwargs['sSearch'].decode('utf-8')
        if search_string:
            expenses_query = expenses_query.filter(or_(self.Expense.nature.like('%' + search_string + '%'),
                                                       self.Legislator.name.like('%' + search_string + '%'),
                                                       self.Legislator.party.like('%' + search_string + '%'),
                                                       self.Supplier.name.like('%' + search_string + '%'),
                                                       self.Supplier.cnpj.like('%' + search_string + '%')))
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
        session = self.Session()

        start = int(kwargs['iDisplayStart'])
        end = start + int(kwargs['iDisplayLength'])
        sort_column = str(int(kwargs['iSortCol_0']) + 1) # sqlalchemy starts counting from 1

        if kwargs['sSortDir_0'] == 'asc':
            sort_order = asc
        else:
            sort_order = desc

        legislator = session.query(self.Legislator).get(legislator_id)
        expenses_query = session.query(self.Expense.nature, self.Supplier.name, self.Supplier.cnpj,
                                       self.Expense.number, self.Expense.date, self.Expense.expensed
                                       ).join('supplier').order_by(sort_order(sort_column))

        expenses_query = expenses_query.filter(self.Expense.legislator == legislator)

        total_results = expenses_query.count()

        search_string = kwargs['sSearch'].decode('utf-8')
        if search_string:
            expenses_query = expenses_query.filter(or_(self.Expense.nature.like('%' + search_string + '%'),
                                                       self.Supplier.name.like('%' + search_string + '%'),
                                                       self.Supplier.cnpj.like('%' + search_string + '%')))
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

    def legislator_info(self, legislator_id):
        session = self.Session()
        legislator = session.query(self.Legislator).get(legislator_id)
        response = dict(legname = legislator.name, legparty = legislator.party)
        return unicode(json.dumps(response))
    legislator_info.exposed = True

    def legislator_trivia(self, legislator_id):
        session = self.Session()

        suppliers = session.query(self.Supplier.name, func.sum(self.Expense.expensed))\
            .join('expenses')\
            .filter_by(legislator_id = legislator_id)\
            .group_by(self.Supplier.name)\
            .order_by(desc('2')).limit(5).all()

        response = dict(biggest_suppliers = suppliers)
        return unicode(json.dumps(response))
    legislator_trivia.exposed = True

    def per_legislator(self):
        session = self.Session()

        expenses = session.query(self.Legislator.id, self.Legislator.name, self.Legislator.party,
                                 func.sum(self.Expense.expensed)).join('expenses').group_by(self.Legislator.party, self.Legislator.name).order_by(desc('3')).all()

        data = []
        for exp in expenses:
            line = []
            line.append('<a class="navigation" href="/legislador/%d">%s</a>' % (exp[0], exp[1]))
            line += exp[2:]
            data.append(line)

        columns = []
        columns.append(dict(label = u'Parlamentar', type = 'string', index = 0))
        columns.append(dict(label = u'Partido', type = 'string', index = 1))
        columns.append(dict(label = u'Valor ressarcido', type = 'money', index = 2))
        return self._make_response(columns, data, show_graph = False)
    per_legislator.exposed = True

    def per_party(self):
        session = self.Session()

        expenses = session.query(self.Legislator.party, func.count(func.distinct(self.Legislator.name)),
                                 func.sum(self.Expense.expensed)).join('expenses').group_by(self.Legislator.party).all()

        expenses = [[party, num_legislators, expensed, expensed / num_legislators]
                     for party, num_legislators, expensed in expenses]

        expenses.sort(cmp = lambda x, y: cmp(y[3], x[3]))

        columns = []
        columns.append(dict(label = u'Partido', type = 'string', index = 0))
        columns.append(dict(label = u'Parlamentares', type = 'number', index = 1))
        columns.append(dict(label = u'Valor ressarcido', type = 'money', index = 2))
        columns.append(dict(label = u'Média', type = 'money', index = 3, skip_total = True))

        graph_title = u'Gasto médio por partido'
        return self._make_response(columns, expenses, graph_title = graph_title)
    per_party.exposed = True

    def per_supplier(self):
        session = self.Session()

        expenses = session.query(self.Supplier.name, self.Supplier.cnpj,
                                 func.sum(self.Expense.expensed)).join('expenses').group_by(self.Supplier.cnpj).order_by(desc('3')).all()

        columns = []
        columns.append(dict(label = u'Empresa/Pessoa', type = 'string', index = 0))
        columns.append(dict(label = u'CNPJ/CPF', type = 'string', index = 1))
        columns.append(dict(label = u'Valor recebido', type = 'money', index = 2))
        return self._make_response(columns, expenses, show_graph = False)
    per_supplier.exposed = True

    def per_nature(self):
        session = self.Session()

        expenses = session.query(self.Expense.nature,
                                 func.sum(self.Expense.expensed)).group_by(self.Expense.nature).all()

        columns = []
        columns.append(dict(label = u'Tipo de gasto', type = 'string', index = 0))
        columns.append(dict(label = u'Valor ressarcido', type = 'money', index = 1))

        graph_title = u'Total de gasto por tipo'
        return self._make_response(columns, expenses, graph_title = graph_title)
    per_nature.exposed = True


class DepWatchWeb(object):
    static = tools.staticdir.handler(section='static',
                                     root=appdir, dir='static')

    def __init__(self, config, models):
        self.config = config
        self.qserver = QueryServer(config, models)


    def index(self):
        return html_data % (self.config)
    index.exposed = True


    def database(self):
        return cherrypy.lib.static.serve_file(os.path.join(project_path, self.config['base_path'], 'data.db'),
                                               'application/octet-stream', 'attachment', self.config['base_path'] + '.db')
    database.exposed = True


    def default(self, *ignored):
        return self.index()
    default.exposed = True

