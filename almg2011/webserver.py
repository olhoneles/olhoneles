#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (©) 2012 Gustavo Noronha Silva
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

from base.webserver import *
from base.models import models


config = dict(
    base_path = 'almg2011',
    title = 'Olho neles! ALMG 2011-2014',
    data_source_uri = 'http://almg.gov.br/',
    data_source_label = 'Assembléia Legislativa do Estado de Minas Gerais'
)


def setup_server():
    cherrypy.config.update({'environment': 'production',
                            'log.screen': False,
                            'show_tracebacks': True})
    cherrypy.tree.mount(DepWatchWeb(config, models))


if __name__ == '__main__':
    cherrypy.quickstart(DepWatchWeb(config, models))
