# -*- coding: utf-8 -*-
#
# Copyright (©) 2010-2013 Gustavo Noronha Silva
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

import json
import re
import time
import urllib
from datetime import datetime, date
from urllib2 import urlopen, Request, URLError, HTTPError
from django.core.management.base import BaseCommand, CommandError
from montanha.models import *


full_scan = False
debug_enabled = False


def debug(message):
    if debug_enabled:
        print message


class BaseCollector(object):
    def update_legislators(self):
        exception("Not implemented.")

    def update_data(self, year=datetime.now().year):
        exception("Not implemented.")

    def retrieve_uri(self, uri, data={}, headers={}):
        resp = None

        while True:
            try:
                if data:
                    req = Request(uri, urllib.urlencode(data), headers)
                else:
                    req = Request(uri, headers=headers)
                resp = urlopen(req)
                break
            except HTTPError, e:
                if e.getcode() != 404:
                    raise HTTPError(e.url, e.code, e.msg, e.headers, e.fp)
            except URLError:
                print "Unable to retrieve %s; will try again in 10 seconds." % (uri)

            time.sleep(10)

        # The JSON returned by ALMG's web service uses the brazilian
        # locale for floating point numbers (uses , instead of .).
        data = re.sub(r"([0-9]+),([0-9]+)", r"\1.\2", resp.read())

        return json.loads(data)


class ALMG(BaseCollector):
    def __init__(self, mandate_start=date(2011, 1, 1)):
        self.mandate_start = mandate_start
        try:
            self.institution = Institution.objects.get(siglum='ALMG')
        except Institution.DoesNotExist:
            self.institution = Institution(siglum='ALMG', u'Assembléia Legislativa do Estado de Minas Gerais')
            self.institution.save()

    def update_legislators(self):
        legislators = self.retrieve_uri("http://dadosabertos.almg.gov.br/ws/deputados/em_exercicio?formato=json")["list"]
        for entry in legislators:
            try:
                legislator = Legislator.objects.get(original_id=entry["id"])
                debug("Found existing legislator: %s" % unicode(legislator))

                try:
                    mandate = Mandate.objects.get(legislator=legislator, date_start=self.mandate_start)
                except Mandate.DoesNotExist:
                    mandate = Mandate(legislator=legislator, date_start=self.mandate_start, party=party, institution=self.institution)
                    mandate.save()
                    debug("Mandate starting on %s did not exist, created." % self.mandate_start.strftime("%F"))

            except Legislator.DoesNotExist:
                legislator = Legislator(name=entry["nome"], original_id=entry["id"])
                legislator.save()

                try:
                    party = PoliticalParty.objects.get(siglum=entry["partido"])
                except PoliticalParty.DoesNotExist:
                    party = PoliticalParty(siglum=entry["partido"])
                    party.save()

                    debug("New party: %s" % unicode(party))

                mandate = Mandate(legislator=legislator, date_start=self.mandate_start, party=party, institution=self.institution)
                mandate.save()

                debug("New legislator found: %s" % unicode(legislator))

    def update_data(self):
        for mandate in Mandate.objects.filter(date_start__year=self.mandate_start.year):
            if full_scan:
                for year in range(self.mandate_start.year, datetime.now().year + 1):
                    self.update_data_for_year(mandate, year)
            else:
                self.update_data_for_year(mandate, datetime.now().year)

    def update_data_for_year(self, mandate, year):
        debug("Updating data for year %d" % year)
        for month in range(1, 13):
            self.update_data_for_month(mandate, year, month)

    def update_data_for_month(self, mandate, year, month):
        debug("Updating data for %d-%d - %s" % (year, month, unicode(mandate)))
        uri = "http://dadosabertos.almg.gov.br/ws/prestacao_contas/verbas_indenizatorias/deputados/%s/%d/%d?formato=json" % (mandate.legislator.original_id, year, month)
        for entry in self.retrieve_uri(uri)["list"]:
            try:
                nature = ExpenseNature.objects.get(original_id=entry["codTipoDespesa"])
            except ExpenseNature.DoesNotExist:
                nature = ExpenseNature(original_id=entry["codTipoDespesa"], name=entry["descTipoDespesa"])
                nature.save()

            for details in entry["listaDetalheVerba"]:
                try:
                    supplier = Supplier.objects.get(identifier=details["cpfCnpj"])
                except Supplier.DoesNotExist:
                    supplier = Supplier(identifier=details["cpfCnpj"], name=details["nomeEmitente"])
                    supplier.save()

                if "descDocumento" in details:
                    number = details["descDocumento"]
                else:
                    debug("No document number, using reference date.")
                    number = details["dataReferencia"]["$"]

                date = details["dataEmissao"]["$"]
                value = details["valorDespesa"]
                expensed = details["valorReembolsado"]

                try:
                    expense = Expense.objects.get(original_id=details["id"],
                                                  number=number,
                                                  nature=nature,
                                                  date=date,
                                                  value=value,
                                                  expensed=expensed,
                                                  mandate=mandate,
                                                  supplier=supplier)
                    debug("Existing expense found: %s" % unicode(expense))
                except Expense.DoesNotExist:
                    expense = Expense(original_id=details["id"],
                                      number=number,
                                      nature=nature,
                                      date=date,
                                      value=value,
                                      expensed=expensed,
                                      mandate=mandate,
                                      supplier=supplier)
                    expense.save()

                    debug("New expense found: %s" % unicode(expense))


class Command(BaseCommand):
    args = "<source> [mandate_start_year]"
    help = "Collects data for a number of sources"

    def handle(self, *args, **options):
        global debug_enabled
        global full_scan

        if "debug" in args:
            debug_enabled = True

        if "full-scan" in args:
            full_scan = True

        if "almg" in args:
            almg = ALMG()
            almg.update_legislators()
            almg.update_data()
