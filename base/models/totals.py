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

from sqlalchemy import Table, Column, Unicode, Integer, Float

from base.models import Base


class TotalsPerNature(Base):
    __tablename__ = 'totals_per_nature'

    nature = Column(Unicode, primary_key = True)
    expensed = Column(Float)

    def __unicode__(self):
        return u'%s - %.2f' % (self.nature, self.expensed)


class TotalsPerLegislator(Base):
    __tablename__ = 'totals_per_legislator'

    id = Column(Integer, primary_key = True)
    name = Column(Unicode)
    party = Column(Unicode)
    expensed = Column(Float)

    def __unicode__(self):
        return u'%s (%s) expensed %.2f' % (self.name, self.party, self.expensed)


class TotalsPerParty(Base):
    __tablename__ = 'totals_per_party'

    party = Column(Unicode, primary_key = True)
    num_legislators = Column(Integer)
    expensed = Column(Float)

    def __unicode__(self):
        return u'%s expensed %.2f' % (self.party, self.expensed)


class TotalsPerSupplier(Base):
    __tablename__ = 'totals_per_supplier'

    cnpj = Column(Unicode, primary_key = True)
    name = Column(Unicode)
    expensed = Column(Float)

    def __unicode__(self):
        return u'%.2f paid to %s (%s)' % (self.expensed, self.name, self.cnpj)

