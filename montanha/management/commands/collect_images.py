# -*- coding: utf-8 -*-
#
# Copyright (©) 2014 Wilson Pinto Júnior
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

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    args = "<source> [debug]"
    help = "Collects data for a number of sources"

    def handle(self, *args, **options):
        collection_runs = []
        debug_enabled = False

        if "debug" in args:
            debug_enabled = True

        if "algo" in args:
            from collectors.algo import ALGO
            algo = ALGO(collection_runs, debug_enabled)
            algo.update_images()
