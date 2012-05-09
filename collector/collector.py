#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (©) 2010, 2011, 2012 Gustavo Noronha Silva
# Copyright (©) 2010, 2011, 2012 Estêvão Samuel Procópio
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

if __name__ == '__main__':
    import os
    os.environ['LANG'] = 'pt_BR.UTF-8'
    os.environ['LC_ALL'] = 'pt_br.UTF-8'

    import optparse

    parser = optparse.OptionParser()
    parser.add_option('-y', '--year', type='int', dest='year', help='Year to collect from.')
    parser.add_option('-s', '--source', type='string', dest='source', help="Source to collect from. Possible values are 'almg', 'cmbh', 'senado', 'camara'")

    (options, args) = parser.parse_args()

    vi = None
    if options.source == 'almg':
        from sources import almgsource
        vi = almg.VerbaIndenizatoriaALMG()
    if options.source == 'cmbh':
        from sources import cmbhsource
        vi = cmbhsource.VerbaIndenizatoriaCMBH()
    if options.source == 'senado':
        from sources import senadosource
        vi = senadosource.VerbaIndenizatoriaSenado()
    if options.source == 'camara':
        from sources import camarasource
        vi = camarasource.VerbaIndenizatoriaCamara()

    if not vi:
        parser.error ('Invalid value for source (%s).' % (options.source))

    vi.update_legislators()

    if options.year:
        vi.update_data(options.year)
    else:
        vi.update_data()

