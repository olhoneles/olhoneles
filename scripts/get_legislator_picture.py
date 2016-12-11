# -*- coding: utf-8 -*-
# Copyright (C) 2013 Marcelo Jorge Vieira <metal@alucinados.com>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public
# License along with this program; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place - Suite 330,
# Boston, MA 02111-1307, USA.
##

import os
import urllib2
import urllib

from BeautifulSoup import BeautifulSoup
from django.core.files import File

from montanha.models import Legislator


SITE_URL = "http://www.almg.gov.br"
PAGE_URL = "%s/%s" % (
    SITE_URL, (
        "/deputados/conheca_deputados/index.html?aba=js_tabAtual"
        "&rdSituacaoAnt=Exercicio&sltResult=0&formato=imagem"
        "&sltLegAnt=16&rdSituacao=Exercicio"
    )
)
req = urllib2.Request(PAGE_URL, headers={"User-Agent": "Mozilla/5.0"})
html = urllib2.urlopen(req)
doc = BeautifulSoup(html)

ul = doc.find("ul", {"id": "deputados_view-imagem"})
for item in ul.findAll("li"):
    try:
        # FIXME
        picture_url = "%s%s" % (SITE_URL, item.find("img")["src"])
        picture_url = picture_url.rsplit("?__scale=w:109,h:120,t:4")[0]

        legislator_name = item.find("p", {"class": "titulo"}).find("a").string
        leg = Legislator.objects.get(name=str(legislator_name))

        result = urllib.urlretrieve(picture_url)
        leg.picture.save(os.path.basename(picture_url), File(open(result[0])))
        leg.save()
        print "{0} => {1}".format(legislator_name, picture_url)
    except Legislator.DoesNotExist:
        pass
