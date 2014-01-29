# -*- coding: utf-8 -*-
#
# Copyright (©) 2010-2013 Gustavo Noronha Silva
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

import signal
import sys

# This hack makes django less memory hungry (it caches queries when running
# with debug enabled.
from django.conf import settings
settings.DEBUG = False

from django.core.management.base import BaseCommand
from django.db import transaction
from montanha.models import ArchivedExpense, Expense


full_scan = False
debug_enabled = False


class Command(BaseCommand):
    args = "<source> [mandate_start_year]"
    help = "Collects data for a number of sources"

    @transaction.commit_manually
    def handle(self, *args, **options):
        global debug_enabled
        global full_scan

        settings.expense_locked_for_collection = True

        collection_runs = []

        if "debug" in args:
            debug_enabled = True

        if "full-scan" in args:
            full_scan = True

        def signal_handler(signal, frame):
            transaction.rollback()
            sys.exit(0)
        signal.signal(signal.SIGINT, signal_handler)

        try:
            if "almg" in args:
                from almg import ALMG
                almg = ALMG(collection_runs, debug_enabled, full_scan)
                almg.update_legislators()
                almg.update_data()
                almg.update_legislators_data()

            if "senado" in args:
                from senado import Senado
                senado = Senado(collection_runs, debug_enabled, full_scan)
                senado.update_legislators()
                senado.update_data()
                senado.update_legislators_extra_data()

            if "cmbh" in args:
                from cmbh import CMBH
                cmbh = CMBH(collection_runs, debug_enabled, full_scan)
                cmbh.update_legislators()
                cmbh.update_data()

            if "cmsp" in args:
                from cmsp import CMSP
                cmsp = CMSP(collection_runs, debug_enabled, full_scan)
                cmsp.update_data()

            settings.expense_locked_for_collection = False

            for run in collection_runs:
                legislature = run.legislature
                Expense.objects.filter(mandate__legislature=legislature).delete()
                for expense in ArchivedExpense.objects.filter(collection_run=run).all():
                    Expense(original_id=expense.original_id,
                            number=expense.number,
                            nature=expense.nature,
                            date=expense.date,
                            value=expense.value,
                            expensed=expense.expensed,
                            mandate=expense.mandate,
                            supplier=expense.supplier).save()
        except Exception:
            transaction.rollback()
            raise

        transaction.commit()
