# -*- coding: utf-8 -*-
#
# Copyright (©) 2010-2014 Gustavo Noronha Silva
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

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db import connection, transaction

from montanha.models import Expense


# This hack makes django less memory hungry (it caches queries when running
# with debug enabled.
settings.DEBUG = False

debug_enabled = False


class Command(BaseCommand):
    help = "Collects data for a number of sources"

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

        collection_runs = []

        debug_enabled = False
        if options.get('debug'):
            debug_enabled = True

        houses_to_consolidate = []

        if 'almg' in options.get('house'):
            from collectors.almg import ALMG
            almg = ALMG(collection_runs, debug_enabled)
            almg.update_legislators()
            almg.update_data()
            almg.update_legislators_data()
            houses_to_consolidate.append("almg")

        if 'algo' in options.get('house'):
            from collectors.algo import ALGO
            almg = ALGO(collection_runs, debug_enabled)
            almg.update_legislators()
            almg.update_data()
            houses_to_consolidate.append("algo")

        if 'senado' in options.get('house'):
            from collectors.senado import Senado
            senado = Senado(collection_runs, debug_enabled)
            senado.update_legislators()
            senado.update_data()
            senado.update_legislators_extra_data()
            houses_to_consolidate.append("senado")

        if 'cmbh' in options.get('house'):
            from collectors.cmbh import CMBH
            cmbh = CMBH(collection_runs, debug_enabled)
            cmbh.update_legislators()
            cmbh.update_data()
            houses_to_consolidate.append("cmbh")

        if 'cmsp' in options.get('house'):
            from collectors.cmsp import CMSP
            cmsp = CMSP(collection_runs, debug_enabled)
            cmsp.update_data()
            houses_to_consolidate.append("cmsp")

        if 'cdep' in options.get('house'):
            from collectors.cdep import CamaraDosDeputados
            cdep = CamaraDosDeputados(collection_runs, debug_enabled)
            cdep.update_legislators()
            cdep.update_data()
            houses_to_consolidate.append("cdep")

        settings.expense_locked_for_collection = False

        for run in collection_runs:
            legislature = run.legislature
            Expense.objects.filter(mandate__legislature=legislature).delete()

            columns = "number, nature_id, date, value, expensed, mandate_id, supplier_id"
            with transaction.atomic():
                cursor = connection.cursor()
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
