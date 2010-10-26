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

    def _make_response(self, columns, data, show_graph = True):
        expenses = []
        total = 0

        for expense in data:
            total += expense[1]
            expenses.append((expense[0], expense[1]))

        expenses.append(('Total', total))

        response = dict(show_graph = show_graph,
                        columns = columns,
                        data = expenses)

        return unicode(json.dumps(response))

    def per_legislator(self):
        session = Session()

        expenses = session.query(Legislator.name,
                                 func.sum(Expense.expensed)).join('expenses').group_by(Legislator.name).order_by(desc(2)).all()

        return self._make_response([u'Deputad@', u'Valor ressarcido'], expenses, show_graph = False)
    per_legislator.exposed = True

    def per_nature(self):
        session = Session()

        expenses = session.query(Expense.nature,
                                 func.sum(Expense.expensed)).group_by(Expense.nature).all()

        return self._make_response([u'Tipo de gasto', u'Valor ressarcido'], expenses)
    per_nature.exposed = True

cherrypy.quickstart(DepWatchWeb())
