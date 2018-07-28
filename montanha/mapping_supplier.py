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

import random
import string

from elasticsearch.helpers import bulk
from elasticsearch_dsl import (
    analyzer, InnerDoc, Date, Document, Keyword, Long, Nested, Text,
    TokenCount, tokenizer,
)
from elasticsearch_dsl.connections import connections


# Define a default Elasticsearch client
connections.create_connection()


character_analyzer = analyzer(
    'character_analyzer',
    tokenizer=tokenizer('character_tokenizer', 'nGram', min_gram=1, max_gram=1),
)

class MainActivity(InnerDoc):
    text = Text()
    code = Text()


class SecondaryActivity(InnerDoc):
    text = Text()
    code = Text()


class Supplier(Document):
    address = Text(fields={'keyword': Keyword()})
    address_complement = Text()
    address_number = Long()
    city = Text()
    date_opened = Date()
    email = Text()
    enterprise_type = Text()
    federative_officer = Text()
    identifier = Text(
        fields={'length': TokenCount(analyzer=character_analyzer)}
    )
    juridical_nature = Text()
    last_change = Date()  # FIXME
    last_update = Date()  # FIXME
    main_activity = Nested(SecondaryActivity)
    name = Text()
    neighborhood = Text()
    phone = Text()
    postal_code = Text()
    secondary_activities = Nested(SecondaryActivity)
    situation = Text()
    situation = Text()
    situation_date = Date()
    situation_reason = Text()
    special_situation = Text()
    special_situation_date = Date()
    state = Text()
    status = Text()
    trade_name = Text()

    class Index:
        name = 'suppliers'
        settings = {
            'number_of_shards': 2,
        }

    def add_main_activity(self, text, code):
        self.main_activity.append(
            MainActivity(text=text, code=code)
        )

    def add_secondary_activity(self, text, code):
        self.secondary_activities.append(
            SecondaryActivity(text=text, code=code)
        )

    def save(self, **kwargs):
        self.meta.id = self.identifier
        return super(Supplier, self).save(**kwargs)

    @classmethod
    def bulk_save(cls, dicts):
        # FIXME
        my_id = ''.join([
            random.choice(string.ascii_letters + string.digits)
            for n in xrange(16)
        ])
        objects = (
            dict(d.to_dict(include_meta=True),
            **{'_id': d.identifier or my_id})
            for d in dicts
        )
        client = connections.get_connection()
        return bulk(client, objects)
