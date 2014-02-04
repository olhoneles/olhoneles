# -*- coding: utf-8 -*-
#
# Copyright (©) 2013, Marcelo Jorge Vieira <metal@alucinados.com>
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

from django.db import models
from django.conf import settings
from django.utils.translation import ugettext as _
from django.contrib.sites.models import Site


class FAQ(models.Model):
    site = models.ForeignKey(
        Site,
        verbose_name=_('Site'),
        default=settings.SITE_ID)
    question = models.TextField(verbose_name=_('Question'), max_length=1000)
    answer = models.TextField(verbose_name=_('Answer'), max_length=5000)
    last_change = models.DateTimeField(
        verbose_name=_('Last Change'),
        auto_now=True)
    date_created = models.DateTimeField(
        verbose_name=_('Date Created'),
        auto_now_add=True)

    class Meta:
        verbose_name = _('FAQ')
        verbose_name_plural = _('FAQ')

    def __unicode__(self):
        return u"%s" % (self.question)
