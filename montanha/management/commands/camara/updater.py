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

from montanha.models import *
from datetime import datetime, date

import os

from django.core.files import File
from django.db.models import Sum


class CamaraUpdater:
    def __init__(self, debug_enabled=False):
        self.debug_enabled = debug_enabled

        try:
            institution = Institution.objects.get(siglum='CDF')
        except Institution.DoesNotExist:
            institution = Institution(siglum='CDF', name=u'Câmara dos Deputados')
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
            legislator = Legislator.objects.get(original_id=leg["original_id"])
            self.debug("Found existing legislator: %s" % unicode(legislator))

            mandate = self.mandate_for_legislator(legislator, party)

        except Legislator.DoesNotExist:
            legislator = Legislator(name=leg["name"], original_id=leg["original_id"])
            legislator.save()

            if 'picture' in leg.keys():
                filename = 'camara-%s' % os.path.basename(leg['picture_uri'])
                self.debug("Saving picture %s for %s (%d)" % (filename, leg['name'], leg['original_id']))
                legislator.picture.save(filename, File(open(leg['picture'])))
                legislator.save()

            mandate = Mandate(legislator=legislator, date_start=self.legislature.date_start,
                              party=party, legislature=self.legislature)
            mandate.save()

            self.debug("New legislator found: %s" % unicode(legislator))

    def update_legislator_picture(self, legislator):
        leg = Legislator.objects.get(original_id=legislator['original_id'])
        leg.picture.save(os.path.basename(legislator['picture_uri']), File(open(legislator['picture'])))
        leg.save()

    def update_expense_natures(self, natures):
        institution = Institution.objects.get(siglum='CDF')

        for nature in natures:
            try:
                nature = ExpenseNature.objects.get(institution=institution, original_id=nature['original_id'])
            except ExpenseNature.DoesNotExist:
                nature = ExpenseNature(institution=institution, original_id=nature['original_id'], name=nature['name'])
                nature.save()

                self.debug("New nature found: %s" % unicode(nature))

    def update_nature_expenses(self, mandate, nature_id, expenses):
        institution = Institution.objects.get(siglum='CDF')
        nature = ExpenseNature.objects.get(institution=institution, original_id=nature_id)

        for expense in expenses:
            try:
                supplier = Supplier.objects.get(identifier=expense["cnpj"])
            except Supplier.DoesNotExist:
                supplier = Supplier(identifier=expense["cnpj"], name=expense["supplier_name"])
                supplier.save()

                self.debug("New supplier found: %s" % unicode(supplier))

            try:
                expense = Expense.objects.get(number=expense['docnumber'],
                                              nature=nature,
                                              date=expense['date'],
                                              value=expense['value'],
                                              expensed=expense['expensed'],
                                              mandate=mandate,
                                              supplier=supplier)
                self.debug("Existing expense found: %s" % unicode(expense))

            except Expense.DoesNotExist:
                expense = Expense(number=expense['docnumber'],
                                  nature=nature,
                                  date=expense['date'],
                                  value=expense['value'],
                                  expensed=expense['expensed'],
                                  mandate=mandate,
                                  supplier=supplier)
                expense.save()

                self.debug("New expense found: %s" % unicode(expense))

    def get_nature_total(self, mandate, nature_id, year, month):
        institution = Institution.objects.get(siglum='CDF')
        nature = ExpenseNature.objects.get(original_id=nature_id)
        try:
            item = Expense.objects.values('nature').filter(mandate=mandate, nature=nature, date__year=year, date__month=month).annotate(total=Sum('expensed'))[0]
            return float(item['total'])
        except:
            return None

    def update_legislator_expenses_per_nature(self, legid, expenses):
        legislator = Legislator.objects.get(original_id=legid)
        self.debug("Found existing legislator: %s" % unicode(legislator))
        mandate = self.mandate_for_legislator(legislator, None)

        for item in expenses:
            try:
                nature = ExpenseNature.objects.get(name=item['nature'])
            except ExpenseNature.DoesNotExist:
                nature = ExpenseNature(name=item['nature'])
                nature.save()

                self.debug("New nature found: %s" % unicode(nature))

            for details in item['expenses']:
                try:
                    supplier = Supplier.objects.get(identifier=details["cnpj"])
                except Supplier.DoesNotExist:
                    supplier = Supplier(identifier=details["cnpj"], name=details["supplier_name"])
                    supplier.save()

                    self.debug("New supplier found: %s" % unicode(supplier))

                try:
                    expense = Expense.objects.get(number=details['docnumber'],
                                                  nature=nature,
                                                  date=details['date'],
                                                  value=details['value'],
                                                  expensed=details['expensed'],
                                                  mandate=mandate,
                                                  supplier=supplier)
                    self.debug("Existing expense found: %s" % unicode(expense))
                except Expense.DoesNotExist:
                    expense = Expense(number=details['docnumber'],
                                      nature=nature,
                                      date=details['date'],
                                      value=details['value'],
                                      expensed=details['expensed'],
                                      mandate=mandate,
                                      supplier=supplier)
                    expense.save()

                    self.debug("New expense found: %s" % unicode(expense))
