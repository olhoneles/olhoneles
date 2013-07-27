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

from django.conf.urls.defaults import patterns, url


urlpatterns = patterns(
    'montanha.views',

    # Index
    url(r'^$', 'show_index', name='index'),

    url(r'(?P<institution>[^/]+)?/?all/$', 'show_all', name='show-all'),

    url(r'(?P<institution>[^/]+)?/?per-nature/$', 'show_per_nature', name='per-nature'),
    url(r'(?P<institution>[^/]+)?/?per-legislator/$', 'show_per_legislator', name='per-legislator'),
    url(r'(?P<institution>[^/]+)?/?per-party/$', 'show_per_party', name='per-party'),
    url(r'(?P<institution>[^/]+)?/?per-supplier/$', 'show_per_supplier', name='per-supplier'),

    url(r'(?P<institution>[^/]+)?/?detail-legislator/(?P<legislator_id>\d+)$', 'show_legislator_detail', name='show-legislator-detail'),
)
