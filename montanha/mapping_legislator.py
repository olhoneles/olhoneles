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

from elasticsearch_dsl import Date, Document, InnerDoc, Nested, Text


class AlternativeName(InnerDoc):
    name = Text()


class Legislator(Document):
    about = Text()
    alternative_names = Nested(AlternativeName)
    date_of_birth = Date()
    email = Text()
    gender = Text()
    identifier = Text()
    name = Text()
    picture = Text()
    site = Text()

    class Index:
        name = 'legislators'
        settings = {
            'number_of_shards': 2,
        }

    def add_alternative_name(self, name):
        self.alternative_names.append(AlternativeName(name=name))

    def save(self, **kwargs):
        self.meta.id = self.identifier
        return super(Legislator, self).save(**kwargs)
