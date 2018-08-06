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

from elasticsearch_dsl import Date, Document, Integer, Text


class CollectionRun(Document):
    institution_siglum = Text()
    legislature_year_start = Integer()
    legislature_year_end = Integer()
    date = Date()

    class Index:
        name = 'collection-run'
        settings = {
            'number_of_shards': 2,
        }

    @classmethod
    def get_or_create(
            cls, date, institution_siglum, legislature_year_start,
            legislature_year_end):

        search = cls.search()
        search = search \
            .filter('term', date=date) \
            .filter('term', institution_siglum=institution_siglum)

        if search.count() > 0:
            return search, False

        collection_run = cls(
            date=date,
            institution_siglum=institution_siglum,
            legislature_year_start=legislature_year_start,
            legislature_year_end=legislature_year_end,
        )
        collection_run.save()
        return collection_run, True
