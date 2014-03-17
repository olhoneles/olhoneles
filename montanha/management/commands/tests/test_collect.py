# -*- coding: utf-8 -*-
#
# Copyright (©) 2014, Marcelo Jorge Vieira <metal@alucinados.com>
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

from StringIO import StringIO

from django.core.management import call_command
from django.test import TestCase


class CollectCommandsTestCase(TestCase):

    def test_command_collect_without_instituiton(self):
        out = StringIO()
        call_command('collect', stdout=out)
        self.assertEqual(out.getvalue(), '')
