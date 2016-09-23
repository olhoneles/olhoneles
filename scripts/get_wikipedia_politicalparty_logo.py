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

from montanha.models import *


for pp in PoliticalParty.objects.all():
    if not pp.wikipedia:
        continue
    req = urllib2.Request(pp.wikipedia, headers={"User-Agent": "Mozilla/5.0"})
    html = urllib2.urlopen(req)
    doc = BeautifulSoup(html)
    table = doc.find("table", {"class": "infobox_v2"})
    if table:
        img = table.find("a", {"class": "image"})
        if img:
            logo_url = img.find("img")["src"]
            if "http:" not in logo_url:
                logo_url = "http:%s" % logo_url
            print logo_url
            result = urllib.urlretrieve(logo_url)
            pp.logo.save(os.path.basename(logo_url), File(open(result[0])))
            pp.save()
