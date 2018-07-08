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
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db import connection, transaction

from montanha.models import Mandate


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

        settings.expense_locked_for_collection = True

        debug_enabled = False
        if options.get('debug'):
            debug_enabled = True

        houses_to_consolidate = []
        for house in options.get('house'):
            module = import_module(
                'montanha.management.commands.collectors.{0}'.format(house)
            )
            command = module.Collector(self.collection_runs, debug_enabled)
            command.run()
            del command
            houses_to_consolidate.append(house)

        settings.expense_locked_for_collection = False

        for run in self.collection_runs:
            legislature = run.legislature
            mandates = Mandate.objects.filter(legislature=legislature)

            with transaction.atomic():
                cursor = connection.cursor()
                for m in mandates:
                    cursor.execute(
                        "delete from montanha_expense where mandate_id=%s", (m.id,)
                    )

                columns = "number, nature_id, date, value, expensed, mandate_id, supplier_id"
                cursor.execute(
                    "insert into montanha_expense (%s) select %s from montanha_archivedexpense where collection_run_id=%d" % (
                        columns, columns, run.id
                    )
                )
                cursor.close()

            run.committed = True
            run.save()

        for house in houses_to_consolidate:
            call_command("consolidate", house)
