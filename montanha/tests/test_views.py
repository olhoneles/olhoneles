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

from django.test import TestCase
from django.test.client import RequestFactory

from montanha.views import show_index, show_robots_txt
from montanha.tests.fixtures import InstitutionFactory


class MontanhaViewTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_render_index_without_institution(self):
        try:
            request = self.factory.get('/')
            response = show_index(request)
        except TypeError as e:
            response = None
            msg = 'show_index() takes exactly 2 arguments (1 given)'
            self.assertEqual(e.message, msg)

        self.assertEqual(response, None)

    def test_render_index_with_empty_institution(self):
        request = self.factory.get('/')
        response = show_index(request, '')
        self.assertEqual(response.status_code, 200)
        self.assertTrue('O olho neles é' in response.content)

    def test_render_index(self):
        institution = InstitutionFactory.create()

        request = self.factory.get('/')
        response = show_index(request, institution.siglum)
        self.assertEqual(response.status_code, 200)
        self.assertFalse('O olho neles é' in response.content)
        self.assertIn(institution.siglum, response.content)

    def test_render_robots_txt(self):
        request = self.factory.get('/robots.txt')
        response = show_robots_txt(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, 'User-Agent: *\nAllow: /\n')
