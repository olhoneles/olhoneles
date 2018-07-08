# -*- coding: utf-8 -*-
#
# Copyright (©) 2010-2014 Gustavo Noronha Silva
# Copyright (©) 2018, Marcelo Jorge Vieira
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

from importlib import import_module

from django.conf import settings
from django.core.management.base import BaseCommand


# This hack makes django less memory hungry (it caches queries when running
# with debug enabled.
settings.DEBUG = False

debug_enabled = False


class Command(BaseCommand):
    help = "Collects data for a number of sources"
    collection_runs = []

    def add_arguments(self, parser):
        parser.add_argument('house', type=str, nargs='+')
        parser.add_argument(
            '--debug',
            action='store_true',
            dest='debug',
            default=False,
        )

    def handle(self, *args, **options):
        global debug_enabled

        debug_enabled = False
        if options.get('debug'):
            debug_enabled = True

        for house in options.get('house'):
            module = import_module(
                'montanha.management.commands.collectors.{0}'.format(house)
            )
            command = module.Collector(self.collection_runs, debug_enabled)
            command.run()
            del command
