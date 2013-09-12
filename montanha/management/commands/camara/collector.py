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

from ..basecollector import *


class CamaraCollector (BaseCollector):
    def retrieve_legislatures(self):
        uri = 'http://www2.camara.leg.br/deputados/pesquisa'
        headers = {
            'Referer': 'http://www.camara.leg.br',
            'Origin': 'http://www.camara.leg.br',
        }

        return BaseCollector.retrieve_uri(self, uri, headers)

    def retrieve_legislators(self, legislature):
        uri = 'http://www.camara.gov.br/internet/deputado/Dep_Lista_foto.asp?'\
            'Legislatura=%s&Partido=QQ&SX=QQ&Todos=None&UF=QQ&condic=QQ&forma=lista'\
            '&nome=&ordem=nome&origem=None' % legislature.original_id
        headers = {
            'Referer': 'http://www2.camara.leg.br/deputados/pesquisa',
            'Origin': 'http://www.camara.leg.br',
        }

        return BaseCollector.retrieve_uri(self, uri, headers)

    def retrieve_legislator_picture(self, legislator):
        result = urlretrieve(legislator['picture_uri'])
        return result[0]

    def retrieve_legislator_id_for_expenses(self, legislator):
        code = unicode(legislator.picture).split('/')[1].split('-')[1].split('_')[0]

        uri = 'http://www.camara.gov.br/cota-parlamentar/consulta-cota-parlamentar?ideDeputado=%s' % (code)
        headers = {
            'Referer': 'http://www.camara.leg.br/internet/Deputado/dep_Detalhe.asp?id=%s' % (legislator.original_id),
            'Origin': 'http://www.camara.leg.br',
        }

        req = Request(uri, headers=headers)
        resp = urlopen(req)
        return int(resp.geturl().split('=')[1])

    def retrieve_total_expenses_per_nature(self, legislator, year, month):
        legid = self.retrieve_legislator_id_for_expenses(legislator)

        uri = 'http://www.camara.gov.br/cota-parlamentar/cota-sumarizado?'\
            'nuDeputadoId=%d&mesAnoConsulta=%s-%s' % (legid, month, year)

        headers = {
            'Referer': 'http://www.camara.gov.br/cota-parlamentar/cota-sumarizado?nuDeputadoId=%d' % legid,
            'Origin': 'http://www.camara.leg.br',
        }

        return BaseCollector.retrieve_uri(self, uri, headers)

    def retrieve_nature_expenses(self, legislator, nature_id, year, month):
        legid = self.retrieve_legislator_id_for_expenses(legislator)

        referer = 'http://www.camara.gov.br/cota-parlamentar/cota-sumarizado?'\
            'nuDeputadoId=%s&mesAnoConsulta=%s-%s' % (legid, month, year)

        uri = 'http://www.camara.gov.br/cota-parlamentar/cota-analitico?'\
            'nuDeputadoId=%s&numMes=%s&numAno=%s&numSubCota=%d' % (legid, month, year, nature_id)

        headers = {
            'Referer': referer,
            'Origin': 'http://www.camara.leg.br',
        }

        return BaseCollector.retrieve_uri(self, uri, headers)

    def retrieve_legislator_expenses_per_nature(self, idleg, year, month):
        referer = 'http://www.camara.gov.br/cota-parlamentar/cota-sumarizado?'\
            'nuDeputadoId=%s&mesAnoConsulta=%s-%s' % (idleg, month, year)

        uri = 'http://www.camara.gov.br/cota-parlamentar/cota-analitico?'\
            'nuDeputadoId=%s&numMes=%s&numAno=%s&numSubCota=' % (idleg, month, year)

        headers = {
            'Referer': referer,
            'Origin': 'http://www.camara.leg.br',
        }

        return BaseCollector.retrieve_uri(self, uri, headers)
