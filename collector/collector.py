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

import sources

if __name__ == '__main__':
    import optparse

    parser = optparse.OptionParser()
    parser.add_option('-y', '--year', type='int', dest='year', help='Year to collect from.')

    (options, args) = parser.parse_args()

    vi = sources.VerbaIndenizatoriaALMG()
    vi.update_legislators()

    if options.year:
        vi.update_data(options.year)
    else:
        vi.update_data()

