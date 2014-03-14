# -*- coding: utf-8 -*-
#
# Copyright (©) 2013 Estêvão Samuel Procópio Amaral
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

import os
from django.core.files import File
from django.db.models import Sum
from montanha.models import *


class CamaraFederalUpdater:
    def __init__(self, debug_enabled=False):
        self.debug_enabled = debug_enabled

        try:
            institution = Institution.objects.get(siglum='CDF')
        except Institution.DoesNotExist:
            institution = Institution(siglum='CDF', name=u'Câmara dos Deputados Federais')
            institution.save()

        try:
            self.legislature = Legislature.objects.all().filter(institution=institution).order_by('-date_start')[0]
        except IndexError:
            self.legislature = None

    def get_legislature(self, legislature_id):
        institution = Institution.objects.get(siglum='CDF')
        return Legislature.objects.get(institution=institution, original_id=legislature_id).order_by('-date_start')

    def last_legislature(self):
        institution = Institution.objects.get(siglum='CDF')
        return Legislature.objects.all().filter(institution=institution).order_by('-date_start')[0]

    def mandate_for_legislator(self, legislator, party):
        try:
            mandate = Mandate.objects.get(legislator=legislator, date_start=self.legislature.date_start)
        except Mandate.DoesNotExist:
            mandate = Mandate(legislator=legislator, date_start=self.legislature.date_start,
                              party=party, legislature=self.legislature)
            mandate.save()
            self.debug("Mandate starting on %s did not exist, created." % self.legislature.date_start.strftime("%F"))
        return mandate

    def get_mandates(self):
        return Mandate.objects.all().filter(legislature=self.legislature)

    def debug(self, message):
        if self.debug_enabled:
            print message

    def update_legislatures(self, legislatures):
        institution = Institution.objects.get(siglum='CDF')

        found = 0
        inserted = 0

        for legis in legislatures:
            try:
                legislature = Legislature.objects.get(institution=institution, original_id=legis['original_id'])
                self.debug("Found existing legislature: %s" % unicode(legislature))
                found += 1

            except Legislature.DoesNotExist:
                legislature = Legislature(original_id=legis["original_id"], institution=institution,
                                          date_start=legis['date_start'], date_end=legis['date_end'])
                legislature.save()

                self.debug("New legislature found: %s" % unicode(legislature))
                inserted += 1

        return {'legislatures': {'found': found, 'inserted': inserted}}

    def update_legislators(self, legislators):
        for leg in legislators:
            self.update_legislator(leg)

    def update_legislator(self, leg):
        try:
            party = PoliticalParty.objects.get(siglum=leg["party"])
        except PoliticalParty.DoesNotExist:
            party = PoliticalParty(siglum=leg["party"])
            party.save()

            self.debug("New party: %s" % unicode(party))

        try:
            legislator = Legislator.objects.get(name=leg["name"])
            self.debug("Found existing legislator: %s" % unicode(legislator))

            mandate = self.mandate_for_legislator(legislator, party)

        except Legislator.DoesNotExist:
            legislator = Legislator(name=leg["name"], original_id=leg["original_id"])
            legislator.save()

            mandate = Mandate(legislator=legislator, date_start=self.legislature.date_start,
                              party=party, legislature=self.legislature)
            mandate.save()

            self.debug("New legislator found: %s" % unicode(legislator))

        if 'picture' in leg.keys():
            filename = 'camarafederal-%s' % os.path.basename(leg['picture_uri'])
            self.debug("Saving picture %s for %s (%d)" % (filename, leg['name'], leg['original_id']))
            legislator.picture.save(filename, File(open(leg['picture'])))
            legislator.save()

    def update_legislator_picture(self, legislator):
        leg = Legislator.objects.get(original_id=legislator['original_id'])
        leg.picture.save(os.path.basename(legislator['picture_uri']), File(open(legislator['picture'])))
        leg.save()

    def normalize_nature_name(self, nature_name):
        if nature_name.startswith(u'Passagens Aéreas ') and nature_name.endswith(u'*'):
            nature_name = u'Passagens Aéreas'

        return nature_name.title()

    def update_expense_natures(self, natures):
        institution = Institution.objects.get(siglum='CDF')

        for nature in natures:
            try:
                nature = ExpenseNature.objects.get(original_id=nature['original_id'])
            except ExpenseNature.DoesNotExist:
                nature = ExpenseNature(original_id=nature['original_id'], name=self.normalize_nature_name(nature['name']))
                nature.save()

                self.debug("New nature found: %s" % unicode(nature))

    def update_nature_expenses(self, mandate, nature_id, expenses):
        institution = Institution.objects.get(siglum='CDF')
        nature = ExpenseNature.objects.get(original_id=nature_id)

        for expense in expenses:
            try:
                supplier = Supplier.objects.get(identifier=expense["cnpj"])
            except Supplier.DoesNotExist:
                supplier = Supplier(identifier=expense["cnpj"], name=expense["supplier_name"])
                supplier.save()

                self.debug("New supplier found: %s" % unicode(supplier))

            expense = ArchivedExpense(number=expense['docnumber'],
                                      nature=nature,
                                      date=expense['date'],
                                      value=expense['value'],
                                      expensed=expense['expensed'],
                                      mandate=mandate,
                                      supplier=supplier,
                                      collection_run=self.collection_run)
            expense.save()

            self.debug("New expense found: %s" % unicode(expense))
