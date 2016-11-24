# -*- coding: utf-8 -*-
#
# Copyright (©) 2010-2013 Gustavo Noronha Silva
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

from django.conf.urls import url, include
from django.conf.urls.static import static
from django.conf import settings
from django.contrib import admin

from montanha.api import __version__


admin.autodiscover()


urlpatterns = [
    # Admin
    url(r'^admin/', include(admin.site.urls)),

    # API
    url(r'api/v0/',
        include('tastypie_swagger.urls', namespace='olhoneles-v0'),
        kwargs={
            'namespace': 'olhoneles-v0',
            'tastypie_api_module': 'montanha.api.urls.api',
            'version': __version__,
        }),
    url(r'^api/', include('montanha.api.urls')),

    # Montanha
    url(r'^', include('montanha.urls',
                      namespace='montanha',
                      app_name='montanha')),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

handler500 = 'montanha.views.error_500'
handler404 = 'montanha.views.error_404'
