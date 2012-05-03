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

from sqlalchemy import Table, Column, Unicode, Integer, String, Date, Float, Sequence, ForeignKey
from sqlalchemy.orm import relationship, backref
from sqlalchemy import func, desc, asc, or_
from base.models import Base

class Expense(Base):
    __tablename__ = 'expenses'

    id = Column(Integer, Sequence('user_id_seq'), primary_key=True)
    number = Column(String)
    nature = Column(Unicode)
    date = Column(Date)
    value = Column(Float)
    expensed = Column(Float)

    legislator_id = Column(Integer, ForeignKey('legislators.id'))

    supplier_cnpj = Column(String, ForeignKey('suppliers.cnpj'))

    def __init__(self, number, nature, date, value, expensed, legislator, supplier):
        self.number = number
        self.nature = nature
        self.date = date
        self.value = value
        self.expensed = expensed
        self.legislator = legislator
        self.supplier = supplier

    def __unicode__(self):
        return u'%f (%s)' % (self.expensed, self.number)

