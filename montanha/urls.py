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

from django.views.generic import TemplateView
from django.conf.urls import patterns, url
from django.views.defaults import page_not_found


urlpatterns = patterns(
    'montanha.views',

    # JSON queries
    url(r'^([^/]+)?/?q/all/?$', 'query_all', name='query-all'),
    url(r'^([^/]+)?/?q/biggest_suppliers/?$', 'query_biggest_suppliers', name='query-biggest-suppliers'),
    url(r'^([^/]+)?/?q/supplier_all/?$', 'query_supplier_all', name='query-supplier-all'),
    url(r'^([^/]+)?/?q/legislator_all/?$', 'query_legislator_all', name='query-legislator-all'),

    url(r'^([^/]+)?/?all/?$', 'show_all', name='show-all'),

    url(r'^([^/]+)?/?per-nature/?$', 'show_per_nature', name='per-nature'),
    url(r'^([^/]+)?/?per-legislator/?$', 'show_per_legislator', name='per-legislator'),
    url(r'^([^/]+)?/?per-party/?$', 'show_per_party', name='per-party'),
    url(r'^([^/]+)?/?per-supplier/?$', 'show_per_supplier', name='per-supplier'),

    url(r'^detail-supplier/(\d+)/?$', 'show_supplier_overview', name='show-supplier-overview'),

    url(r'^([^/]+)?/?detail-legislator/(\d+)/?$', 'show_legislator_detail', name='show-legislator-detail'),
    url(r'^([^/]+)?/?detail-supplier/(\d+)/?$', 'show_supplier_detail', name='show-supplier-detail'),

    # favicon
    url(r'^favicon.ico$', page_not_found, name='page-not-found'),

    # Robots.txt
    (r'^robots\.txt$', TemplateView.as_view(template_name='robots.txt',
                                            content_type='text/plain')),

    # What is expenses?
    url(r'^o-que-e-verba-indenizatoria/?$', 'what_is_expenses', name='what-is-expenses'),

    # Contact us
    url(r'^fale-conosco/?$', 'contact_us', name='contact-us'),

    # Index
    url(r'^([^/]+)?/?$', 'show_index', name='index'),
)
