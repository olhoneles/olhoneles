#!/usr/bin/python
# -*- coding: utf-8 -*-

from sqlalchemy import create_engine
from sqlalchemy import Table, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

engine = create_engine('sqlite:///data.db')
Session = sessionmaker(bind = engine)
Base = declarative_base()

class Legislator(Base):
    __tablename__ = 'legislators'

    id = Column(Integer, primary_key = True)
    name = Column(String)

    def __init__(self, id, name):
        self.id = id
        self.name = name

    def __repr__(self):
        return 'Dep. %s (Matrícula %d)' % (self.name, self.id)

Base.metadata.create_all(engine)
