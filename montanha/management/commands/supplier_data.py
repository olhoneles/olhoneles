# -*- coding: utf-8 -*-
#
# Copyright (c) 2016, Marcelo Jorge Vieira <metal@alucinados.com>
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

from dateutil.parser import parse

import requests
from django.core.management.base import BaseCommand
from django.db import IntegrityError
from django.db.models.functions import Length

from montanha.models import (
    Supplier, SupplierJuridicalNature, SupplierActivity, SupplierSituation
)


class Command(BaseCommand):
    help = 'Update supplier data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--debug',
            action='store_true',
            dest='debug',
            default=False,
        )

        parser.add_argument(
            '--only-empty',
            action='store_true',
            dest='only-empty',
            default=False,
        )

    def debug(self, text):
        if self.debug_enabled:
            print u'{0}'.format(text)

    def update_supplier(self, supplier):
        try:
            receitaws_api_url = 'https://www.receitaws.com.br/v1/cnpj'
            url = '{0}/{1}'.format(receitaws_api_url, supplier.identifier)
            response = requests.get(url, timeout=5)
        except Exception as e:
            self.debug(u'Error on get {0}: {1}'.format(supplier, str(e)))
            return

        if response.status_code > 399:
            self.debug(u'Error on get {0}: {1}'.format(
                supplier, str(response.text)
            ))
            return

        try:
            data = response.json()
        except ValueError as e:
            self.debug(
                u'Error on loads Json for {0}: {1}'.format(supplier, str(e))
            )
            return

        if data.get('nome'):
            supplier.name = data.get('nome')

        supplier.enterprise_type = data.get('tipo')

        if data.get('abertura'):
            supplier.date_opened = parse(data.get('abertura'))

        supplier.special_situation = data.get('situacao_especial')

        if data.get('data_situacao_especial'):
            supplier.special_situation_date = parse(
                data.get('data_situacao_especial')
            )

        if data.get('ultima_atualizacao'):
            supplier.last_update = parse(data.get('ultima_atualizacao'))

        supplier.status = data.get('status')

        if data.get('situacao'):
            situation, _ = SupplierSituation.objects.get_or_create(
                name=data.get('situacao')
            )
            supplier.situation = situation

        if data.get('data_situacao'):
            supplier.situation_date = parse(data.get('data_situacao'))

        supplier.situation_reason = data.get('motivo_situacao')
        supplier.trade_name = data.get('fantasia')
        supplier.phone = data.get('telefone')
        supplier.email = data.get('email')
        supplier.address = data.get('logradouro')

        try:
            supplier.address_number = int(data.get('numero'))
        except (TypeError, ValueError):
            pass

        supplier.address_complement = data.get('complemento')
        supplier.postal_code = data.get('cep')
        supplier.neighborhood = data.get('bairro')
        supplier.city = data.get('municipio')
        supplier.state = data.get('uf')
        supplier.federative_officer = data.get('efr')

        juridical_nature = data.get('natureza_juridica')
        if juridical_nature:
            code, name = juridical_nature.split(' - ')
            try:
                jn, _ = SupplierJuridicalNature.objects.get_or_create(
                    code=code.strip(),
                    name=name.strip(),
                )
            except IntegrityError:
                jn = SupplierJuridicalNature.objects.get(
                    code=code.strip(),
                )
            supplier.juridical_nature = jn

        main_activity = data.get('atividade_principal')
        if main_activity:
            try:
                ma, _ = SupplierActivity.objects.get_or_create(
                    name=main_activity[0].get('text').strip(),
                    code=main_activity[0].get('code').strip(),
                )
            except IntegrityError:
                ma = SupplierActivity.objects.get(
                    code=main_activity[0].get('code').strip(),
                )
            supplier.main_activity = ma

        secondary_activities = data.get('atividades_secundarias')
        if secondary_activities:
            for x in secondary_activities:
                sa, _ = SupplierActivity.objects.get_or_create(
                    name=x.get('text'),
                    code=x.get('code'),
                )
                supplier.secondary_activities.add(sa)

        supplier.save()

        self.debug(u'Updated info for: {0}'.format(supplier))

    def handle(self, *args, **options):
        self.debug_enabled = True if options.get('debug') else False

        # CNPJ suppliers
        suppliers = Supplier.objects \
            .annotate(identifier_len=Length('identifier')) \
            .filter(identifier_len__gte=14) \
            .exclude(status='ERROR')

        if options.get('only-empty'):
            suppliers = suppliers.filter(address__isnull=True)

        self.debug(u'Total of Suppliers {0}'.format(suppliers.count()))

        for supplier in suppliers:
            self.update_supplier(supplier)
