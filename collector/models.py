#!/usr/bin/python
# -*- coding: utf-8 -*-

from sqlalchemy import create_engine
from sqlalchemy import Table, Column, Unicode, Integer, String, Date, Float, Sequence, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, backref

engine = create_engine('sqlite:///data.db')
Session = sessionmaker(bind = engine)
Base = declarative_base()

class Legislator(Base):
    __tablename__ = 'legislators'

    id = Column(Integer, primary_key = True)
    name = Column(Unicode)

    expenses = relationship('Expense',
                            backref = backref('legislator')
                            )

    def __init__(self, id, name):
        self.id = id
        self.name = name

    def __unicode__(self):
        return u'Dep. %s (Matrícula %d)' % (self.name, self.id)


class Supplier(Base):
    __tablename__ = 'suppliers'

    cnpj = Column(String, primary_key = True)
    name = Column(Unicode)

    expenses = relationship('Expense',
                            backref = backref('supplier')
                            )

    def __init__(self, cnpj, name):
        self.cnpj = cnpj
        self.name = name

    def __unicode__(self):
        return u'%s (CNPJ: %s)' % (self.name, self.cnpj)


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


Base.metadata.create_all(engine)
