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

import urllib2
from BeautifulSoup import BeautifulSoup

from montanha.models import *


SITE_URL = "http://pt.wikipedia.org"
PAGE_URL = "%s/wiki/%s" % (SITE_URL,
                           "Anexo:Lista_de_partidos_pol%C3%ADticos_no_Brasil")


req = urllib2.Request(PAGE_URL, headers={"User-Agent": "Mozilla/5.0"})
html = urllib2.urlopen(req)
doc = BeautifulSoup(html)

table = doc.find("span", {"id": "Partidos_ativos"}).findNext("table")

trs = table.findAll("tr")
for line in trs:
    siglum = line.findNext("td").findNext("td").string
    name = line.findNext("td").findNext("a").string
    wikipedia = SITE_URL + line.findNext("td").find("a")["href"]
    try:
        pp = PoliticalParty.objects.get(siglum=siglum)
        pp.name = name
        pp.wikipedia = wikipedia
        pp.save()
    except PoliticalParty.DoesNotExist:
        pass
