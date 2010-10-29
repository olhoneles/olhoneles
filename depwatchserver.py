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
from sqlalchemy import func, desc
import json

from collector.models import Legislator, Expense, Session


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

    def _make_response(self, columns, data, graph_column = None, show_graph = True):
        if graph_column is None:
            graph_column = len(columns) - 1

        last_line = [ 'Total' ]
        for index, column in enumerate(columns[1:], 1):
            if column['type'] == 'money' or column['type'] == 'number':
                total = 0
                for expense in data:
                    total += expense[index]
                last_line.append(total)
            else:
                last_line.append('')

        response = dict(graph_column = graph_column,
                        show_graph = show_graph,
                        columns = columns,
                        data = data + [last_line])

        return unicode(json.dumps(response))

    def per_legislator(self):
        session = Session()

        expenses = session.query(Legislator.name, Legislator.party,
                                 func.sum(Expense.expensed)).join('expenses').group_by(Legislator.party, Legislator.name).order_by(desc(3)).all()

        columns = []
        columns.append(dict(label = u'Deputad@', type = 'string', index = 0))
        columns.append(dict(label = u'Partido', type = 'string', index = 1))
        columns.append(dict(label = u'Valor ressarcido', type = 'money', index = 2))
        return self._make_response(columns, expenses, show_graph = False)
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
        columns.append(dict(label = u'Média', type = 'money', index = 3))
        return self._make_response(columns, expenses)
    per_party.exposed = True

    def per_nature(self):
        session = Session()

        expenses = session.query(Expense.nature,
                                 func.sum(Expense.expensed)).group_by(Expense.nature).all()

        columns = []
        columns.append(dict(label = u'Tipo de gasto', type = 'string', index = 0))
        columns.append(dict(label = u'Valor ressarcido', type = 'money', index = 1))
        return self._make_response(columns, expenses)
    per_nature.exposed = True

cherrypy.quickstart(DepWatchWeb())
