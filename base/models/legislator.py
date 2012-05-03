#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (©) 2010, 2012 Gustavo Noronha Silva
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

from sqlalchemy import Table, Column, Unicode, Integer
from sqlalchemy.orm import relationship, backref
from base.models import Base


class Legislator(Base):
    __tablename__ = 'legislators'

    id = Column(Integer, primary_key = True)
    name = Column(Unicode)
    party = Column(Unicode)
    position = Column(Unicode)

    expenses = relationship('Expense',
                            backref = backref('legislator')
                            )

    def __init__(self, id, name, party, position):
        self.id = id
        self.name = name
        self.party = party
        self.position = position

    def __unicode__(self):
        return u'Dep. %s (Matrícula %d) - %s' % (self.name, self.id, self.party)

