# -*- coding: utf-8 -*-
#
# Copyright (©) 2013 Marcelo Jorge Vieira <metal@alucinados.com>
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

from django.conf.urls import patterns, url


urlpatterns = patterns(
    'montanha.views',

    # Index
    url(r'^(no:[^/]+)?/?$', 'show_index', name='index'),

    url(r'^all/(no:[^/]+)?/?$', 'show_all', name='show-all'),

    url(r'^([^/]+)?/?per-nature/?$', 'show_per_nature', name='per-nature'),
    url(r'^per-legislator/(no:[^/]+)?/?$', 'show_per_legislator', name='per-legislator'),
    url(r'^per-party/(no:[^/]+)?/?$', 'show_per_party', name='per-party'),
    url(r'^per-supplier/(no:[^/]+)?/?$', 'show_per_supplier', name='per-supplier'),

    url(r'^detail-legislator/(\d+)/(no:[^/]+)?/?$', 'show_legislator_detail', name='show-legislator-detail'),
    url(r'^detail-supplier/(\d+)/(no:[^/]+)?/?$', 'show_supplier_detail', name='show-supplier-detail'),

    # What is expenses?
    url(r'^o-que-e-verba-indenizatoria/(no:[^/]+)?/?$', 'what_is_expenses', name='what-is-expenses'),

    # Contact us
    url(r'^fale-conosco/(no:[^/]+)?/?$', 'contact_us', name='contact-us'),
)
