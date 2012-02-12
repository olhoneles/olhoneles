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

import optparse
import os.path
import csv
import sources
from models import *

if __name__ == '__main__':
    project_path = os.getcwd()

    parser = optparse.OptionParser()
    parser.add_option('-y', '--year', type='int', dest='year', help='Year to collect from.')

    Session = initialize ('sqlite:///%s/data.db' % (project_path))
    session = Session()
    query = session.query(Expense.nature, Legislator.name, Legislator.party,
                          Supplier.name.label('supplier'), Supplier.cnpj, Expense.number,
                          Expense.date, Expense.expensed
                          ).join('legislator').join('supplier').order_by('8')

    outfile = open('dump.csv', 'wb')
    outfile.write('\xef\xbb\xbf');
    outcsv = csv.writer(outfile, 'excel-tab')

    [ outcsv.writerow([
                curr.party,
                curr.name.encode('utf-8'),
                curr.number.encode('utf-8'),
                curr.nature.encode('utf-8'),
                curr.supplier.encode('utf-8'),
                "'" + curr.cnpj,
                curr.date,
                str(curr.expensed).replace('.', ','),
                curr.number.encode('utf-8')]) for curr in query ]

    outfile.close()
