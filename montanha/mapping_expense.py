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

from elasticsearch.helpers import bulk
from elasticsearch_dsl import Date, Document, Float, Integer, Text
from elasticsearch_dsl.connections import connections


# Define a default Elasticsearch client
connections.create_connection()


class Expense(Document):
    city = Text()
    date = Date()
    document_value = Float()
    institution_siglum = Text()
    legislator = Text()
    legislature_year_start = Integer()
    legislature_year_end = Integer()
    mandate = Text()
    month = Text()
    nature = Text()
    original_id = Text()
    political_party_name = Text()
    political_party_siglum = Text()
    refund_value = Float()
    source = Text()
    state_siglum = Text()
    supplier_identifier = Text()
    supplier_name = Text()

    class Index:
        name = 'expenses'
        settings = {
            'number_of_shards': 2,
        }

    @classmethod
    def index_name(cls, institution_siglum, legislature_year_start):
        return 'expenses-{0}-{1}'.format(
            institution_siglum,
            legislature_year_start
        )

    def save(self, **kwargs):
        kwargs['index'] = Expense.index_name(
            self.institution_siglum,
            self.legislature_year_start
        )
        return super(Expense, self).save(**kwargs)

    @classmethod
    def bulk_save(cls, dicts):
        # FIXME
        objects = (
            dict(
                d.to_dict(include_meta=True),
                **{'_index': cls.index_name(
                    d.institution_siglum,
                    int(d.legislature_year_start)
                )}
            )
            for d in dicts
        )

        client = connections.get_connection()
        return bulk(client, objects)
