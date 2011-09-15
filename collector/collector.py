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
    parser.add_option('-s', '--source', type='string', dest='source', default='all', help="Source to collect from. Possible values are 'almg', 'senado', 'camara' or 'all'. The default value for this parameter is 'all'")

    (options, args) = parser.parse_args()

    src = []
    if options.source == 'almg' or options.source == 'all':
        src.append(sources.VerbaIndenizatoriaALMG())
    if options.source == 'senado' or options.source == 'all':
        src.append(sources.VerbaIndenizatoriaSenado())
    if options.source == 'camara' or options.source == 'all':
        src.append(sources.VerbaIndenizatoriaCamara())

    if len(src) == 0:
        parser.error ('Invalid value for source (%s).' % (options.source))

    for vi in src:
        #vi.update_legislators()

        if options.year:
            vi.update_data(options.year)
        else:
            vi.update_data()

