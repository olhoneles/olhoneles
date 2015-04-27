# -*- coding: utf-8 -*-
#
# Copyright (©) 2010-2013 Estêvão Samuel Procópio
# Copyright (©) 2010-2013 Gustavo Noronha Silva
# Copyright (©) 2013 Marcelo Jorge Vieira
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
import datetime
from basecollector import BaseCollector
from datetime import datetime
from montanha.models import *


class ALMG(BaseCollector):
    def __init__(self, collection_runs, debug_enabled=False):
        super(ALMG, self).__init__(collection_runs, debug_enabled)

        try:
            institution = Institution.objects.get(siglum='ALMG')
        except Institution.DoesNotExist:
            institution = Institution(siglum='ALMG', name=u'Assembléia Legislativa do Estado de Minas Gerais')
            institution.save()

        self.legislature, _ = Legislature.objects.get_or_create(institution=institution,
                                                                date_start=datetime(2015, 1, 1),
                                                                date_end=datetime(2018, 12, 31))

    def post_process_uri(self, contents):
        # The JSON returned by ALMG's web service uses the brazilian
        # locale for floating point numbers (uses , instead of .).
        data = re.sub(r"([0-9]+),([0-9]+)", r"\1.\2", contents)
        return json.loads(data)

    def try_name_disambiguation(self, name):
        if name == 'Luiz Henrique':
            try:
                return Legislator.objects.get(id=52), False
            except Legislator.DoesNotExist:
                return None, False

        return None, False

    def update_legislators(self):
        for situation in ['em_exercicio', 'que_exerceram_mandato']:
            legislators = self.retrieve_uri("http://dadosabertos.almg.gov.br/ws/deputados/%s?formato=json" % situation)["list"]
            for entry in legislators:
                try:
                    party = PoliticalParty.objects.get(siglum=entry["partido"])
                except PoliticalParty.DoesNotExist:
                    party = PoliticalParty(siglum=entry["partido"])
                    party.save()

                    self.debug("New party: %s" % unicode(party))

                legislator, created = self.try_name_disambiguation(entry['nome'])
                if not legislator:
                    legislator, created = Legislator.objects.get_or_create(name=entry['nome'])

                if created:
                    self.debug("New legislator: %s" % unicode(legislator))
                else:
                    self.debug("Found existing legislator: %s" % unicode(legislator))

                mandate = self.mandate_for_legislator(legislator, party, original_id=entry["id"])

    def update_legislators_data(self):

        mandates = self.legislature.mandate_set.all()
        for mandate in mandates:
            original_id = mandate.original_id
            uri = "http://dadosabertos.almg.gov.br/ws/deputados/%s?formato=json" % original_id
            entry = self.retrieve_uri(uri)["deputado"]

            self.debug("Legislator %s" % unicode(mandate.legislator))

            if "sexo" in entry:
                mandate.legislator.gender = entry["sexo"]

            if "sitePessoal" in entry:
                mandate.legislator.site = entry["sitePessoal"]

            if "vidaProfissionalPolitica" in entry:
                mandate.legislator.about = entry["vidaProfissionalPolitica"]

            if "emails" in entry and entry["emails"]:
                email = entry["emails"][0]['endereco']
                mandate.legislator.email = "%s%s" % (email, "@almg.gov.br")

            if "dataNascimento" in entry:
                date_of_birth = entry["dataNascimento"]
                # Removed crazy char º
                crazy_char = "º".decode("utf-8")
                if crazy_char in date_of_birth:
                    date_of_birth = date_of_birth.replace(crazy_char, "")
                date_of_birth = datetime.strptime(date_of_birth,
                                                  "%d/%m/%Y").date()
                mandate.legislator.date_of_birth = date_of_birth

            mandate.legislator.save()

    def update_data_for_year(self, mandate, year):
        self.debug("Updating data for year %d" % year)
        for month in range(1, 13):
            self.update_data_for_month(mandate, year, month)

    def update_data_for_month(self, mandate, year, month):
        self.debug("Updating data for %d-%d - %s" % (year, month, unicode(mandate)))
        uri = "http://dadosabertos.almg.gov.br/ws/prestacao_contas/verbas_indenizatorias/deputados/%s/%d/%d?formato=json" % (mandate.original_id, year, month)
        for entry in self.retrieve_uri(uri)["list"]:
            try:
                nature = ExpenseNature.objects.get(original_id=entry["codTipoDespesa"])
            except ExpenseNature.DoesNotExist:
                nature = ExpenseNature(original_id=entry["codTipoDespesa"], name=entry["descTipoDespesa"])
                nature.save()

            for details in entry["listaDetalheVerba"]:
                cnpj = self.normalize_cnpj_or_cpf(details["cpfCnpj"])
                try:
                    supplier = Supplier.objects.get(identifier=cnpj)
                except Supplier.DoesNotExist:
                    supplier = Supplier(identifier=cnpj, name=details["nomeEmitente"])
                    supplier.save()

                if "descDocumento" in details:
                    number = details["descDocumento"]
                else:
                    self.debug("No document number, using reference date.")
                    number = details["dataReferencia"]["$"]

                date = details["dataEmissao"]["$"]
                value = details["valorDespesa"]
                expensed = details["valorReembolsado"]

                expense = ArchivedExpense(original_id=details["id"],
                                          number=number,
                                          nature=nature,
                                          date=date,
                                          value=value,
                                          expensed=expensed,
                                          mandate=mandate,
                                          supplier=supplier,
                                          collection_run=self.collection_run)
                expense.save()

                self.debug("New expense found: %s" % unicode(expense))
