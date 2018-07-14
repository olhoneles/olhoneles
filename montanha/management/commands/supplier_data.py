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

import logging
from datetime import datetime
from dateutil.parser import parse

import requests
from django.conf import settings
from django.core.management.base import BaseCommand

from montanha.mapping_supplier import Supplier as SupplierES
from montanha.models import Supplier as SupplierMySQL


logger = logging.getLogger(__name__)


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

        parser.add_argument(
            '--migrate-from-mysql',
            action='store_true',
            dest='migrate-from-mysql',
            default=False,
        )


    def update_supplier(self, supplier):
        try:
            receitaws_api_url = 'https://www.receitaws.com.br/v1/cnpj'
            url = '{0}/{1}'.format(receitaws_api_url, supplier.identifier)
            response = requests.get(url, timeout=5)
        except Exception as e:
            logger.debug(u'Error on get {0}: {1}'.format(
                supplier.identifier, str(e))
            )
            return

        if response.status_code > 399:
            logger.debug(u'Error on get {0}: {1}'.format(
                supplier.identifier, str(response.text)
            ))
            return

        try:
            data = response.json()
        except ValueError as e:
            logger.debug(
                u'Error on loads Json for {0}: {1}'.format(
                    supplier.identifier, str(e)
                )
            )
            return

        try:
            address_number = float(data.get('numero'))
        except (TypeError, ValueError):
            address_number = None

        try:
            special_situation_date= parse(data.get('data_situacao_especial'))
        except ValueError:
            special_situation_date = None

        supplier.address = data.get('logradouro')
        supplier.address_complement = data.get('complemento')
        supplier.address_number = address_number
        supplier.city = data.get('municipio')
        supplier.date_opened = parse(data.get('abertura'))
        supplier.email = data.get('email')
        supplier.enterprise_type = data.get('tipo')
        supplier.federative_officer = data.get('efr')
        supplier.juridical_nature = data.get('natureza_juridica')
        supplier.last_change = datetime.utcnow()  # FIXME utc?
        supplier.last_update = parse(data.get('ultima_atualizacao'))  # FIXME utc?
        for activity in data.get('atividade_principal'):
            supplier.add_main_activity(activity['text'], activity['code'])
        supplier.name = data.get('nome')
        supplier.neighborhood = data.get('bairro')
        supplier.phone = data.get('telefone')
        supplier.postal_code = data.get('cep')
        for activity in data.get('atividades_secundarias'):
            supplier.add_secondary_activity(activity['text'], activity['code'])
        supplier.situation = data.get('situacao')
        supplier.situation_date = parse(data.get('data_situacao'))
        supplier.situation_reason = data.get('motivo_situacao')
        supplier.special_situation = data.get('situacao_especial')
        supplier.special_situation_date = special_situation_date
        supplier.state = data.get('uf')
        supplier.status = data.get('status')
        supplier.trade_name = data.get('fantasia')

        supplier.save()

        logger.debug(u'Updated info for: {0}'.format(supplier.name))

    def from_mysql_to_es(self):
        logger.debug(u'Importing data from MySQL')

        documents = []

        SupplierES.init()

        suppliers = SupplierMySQL.objects.all()
        for supplier in suppliers:
            try:
                address_number = int(supplier.address_number)
            except (TypeError, ValueError):
                address_number = None
            if supplier.situation:
                situation = supplier.situation.name
            else:
                situation = ''
            if supplier.juridical_nature:
                juridical_nature = supplier.juridical_nature.name
            else:
                juridical_nature = ''
            if supplier.main_activity:
                main_activity = {'text': supplier.main_activity.name}
            else:
                main_activity = []
            if supplier.secondary_activities.count() > 0:
                secondary_activities = [
                    {'text': s.name, 'code': s.code}
                    for s in supplier.secondary_activities.all()
                ]
            else:
                secondary_activities = []

            supplier_es = SupplierES(
                name = supplier.name,
                identifier = supplier.identifier,
                date_opened = supplier.date_opened,
                trade_name = supplier.trade_name,
                status = supplier.status,
                situation = situation,
                situation_date = supplier.situation_date,
                situation_reason = supplier.situation_reason,
                special_situation = supplier.special_situation,
                special_situation_date = supplier.special_situation_date,
                enterprise_type = supplier.enterprise_type,
                federative_officer = supplier.federative_officer,
                address = supplier.address,
                address_number = address_number,
                juridical_nature = juridical_nature,
                address_complement = supplier.address_complement,
                postal_code = supplier.postal_code,
                state = supplier.state,
                city = supplier.city,
                neighborhood = supplier.neighborhood,
                phone = supplier.phone,
                main_activity = main_activity,
                secondary_activities = secondary_activities,
                last_change = supplier.last_change,  # FIXME utc?
                last_update = supplier.last_update,  # FIXME utc?
                email = supplier.email,
            )
            documents.append(supplier_es)
            if len(documents) == settings.ES_OBJECT_LIST_MAXIMUM_COUNTER:
                SupplierES.bulk_save(documents)
                documents = []
                logger.debug(
                    'Added {0} items'.format(
                        settings.ES_OBJECT_LIST_MAXIMUM_COUNTER
                    )
                )

        if documents:
            SupplierES.bulk_save(documents)
            logger.debug('Added {0} items'.format(len(documents)))
            documents = []


    def handle(self, *args, **options):
        if options.get('debug'):
            logger.setLevel(logging.DEBUG)

        if options.get('migrate-from-mysql'):
            self.from_mysql_to_es()
            return

        suppliers = SupplierES.search()
        # exclude(status='ERROR')
        suppliers = suppliers.filter("term", identifier__length=14)

        if options.get('only-empty'):
            suppliers = suppliers.filter("term", address__keyword='')

        for supplier in suppliers:
            logger.debug(u'Updating supplier {0}'.format(supplier.identifier))
            self.update_supplier(supplier)
