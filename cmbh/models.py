#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (©) 2012 Gustavo Noronha Silva
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

from sqlalchemy import Table, Column, Unicode, Integer, Sequence
from sqlalchemy.orm import relationship, backref

from base.models import Base, initialize
from base.models.expense import Expense
from base.models.supplier import Supplier
from base.models.totals import TotalsPerNature, TotalsPerLegislator, TotalsPerParty, TotalsPerSupplier


class Legislator(Base):
    __tablename__ = 'legislators'

    id = Column(Integer, Sequence('legislator_id_seq'), primary_key = True)
    name = Column(Unicode)
    party = Column(Unicode)
    position = Column(Unicode)

    expenses = relationship('Expense',
                            backref = backref('legislator')
                            )

    def __init__(self, id, name, party, position, original_id = None):
        if id:
            self.id = id

        self.name = name
        self.party = party
        self.position = position

        if original_id:
            self.original_id = original_id

    def __unicode__(self):
        return u'Dep. %s (Matrícula %d) - %s' % (self.name, self.id, self.party)

