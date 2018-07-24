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

from elasticsearch_dsl import Document, Text


class PoliticalParty(Document):
    logo = Text()
    name = Text()
    siglum = Text()
    wikipedia = Text()

    class Index:
        name = 'political-parties'
        settings = {
            'number_of_shards': 2,
        }

    def save(self, **kwargs):
        self.meta.id = self.siglum
        return super(PoliticalParty, self).save(**kwargs)
