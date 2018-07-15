# -*- coding: utf-8 -*-
#
# Copyright (c) 2018, Marcelo Jorge Vieira
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

from elasticsearch_dsl import Date, Document, InnerDoc, Nested, Q, Text


class Legislature(InnerDoc):
    date_start = Date()
    date_end = Date()


class Institution(Document):
    name = Text()
    siglum = Text()
    logo = Text()
    legislatures = Nested(Legislature)

    class Index:
        name = 'institutions'
        settings = {
            'number_of_shards': 2,
        }

    def add_legislature(self, date_start, date_end):
        self.legislatures.append(
            Legislature(date_start=date_start, date_end=date_end)
        )

    def save(self, **kwargs):
        self.meta.id = self.siglum
        return super(Institution, self).save(**kwargs)

    @classmethod
    def get_or_create(cls, name, siglum):
        institution = cls.search()
        institution = institution.filter('term', siglum=siglum)
        if institution.count() == 0:
            institution = cls(name=name, siglum=siglum)
            institution.save()
            return institution, True
        return cls.get(id=siglum), False

    def has_legislature(self, date_start, date_end):
        date_start = Q('term', legislatures__date_start=date_start)
        date_end = Q('term', legislatures__date_end=date_end)
        q = Q('term', siglum=self.siglum)
        q &= Q('nested', path='legislatures', query=(date_start & date_end))
        institution = self.search().query(q)
        if institution.count() == 0:
            return False
        return True
