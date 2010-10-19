import locale
import os
import os.path

import cherrypy
from cherrypy import tools
from sqlalchemy import func
import json

from collector.models import Expense, Session


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
        return 'Hi!'
    index.exposed = True

    def per_nature(self):
        session = Session()

        expenses = session.query(Expense.nature,
                                 func.sum(Expense.expensed)).group_by(Expense.nature).all()

        tmp = expenses
        expenses = []
        total = 0

        for expense in tmp:
            total += expense[1]
            expenses.append((expense[0], locale.currency(expense[1])))

        expenses.append(('Total', locale.currency(total)))

        return unicode(json.dumps(expenses))
    per_nature.exposed = True

cherrypy.quickstart(DepWatchWeb())
