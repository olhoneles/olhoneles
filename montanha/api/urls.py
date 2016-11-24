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

from tastypie.api import Api

from montanha.api.resources import (
    SupplierResource, SupplierActivityResource, JuridicalNatureResource,
    PoliticalPartyResource, LegislatorResource, InstitutionResource,
    AlternativeLegislatorNameResource, LegislatureResource, MandateResource,
    ExpenseNatureResource, ExpenseResource, PerNatureResource,
    PerNatureByYearResource, PerNatureByMonthResource, PerLegislatorResource,
    BiggestSupplierForYearResource
)


api = Api(api_name='v0')
api.register(SupplierResource(), canonical=True)
api.register(SupplierActivityResource(), canonical=True)
api.register(JuridicalNatureResource(), canonical=True)
api.register(PoliticalPartyResource(), canonical=True)
api.register(LegislatorResource(), canonical=True)
api.register(AlternativeLegislatorNameResource(), canonical=True)
api.register(InstitutionResource(), canonical=True)
api.register(LegislatureResource(), canonical=True)
api.register(MandateResource(), canonical=True)
api.register(ExpenseNatureResource(), canonical=True)
api.register(ExpenseResource(), canonical=True)
api.register(PerNatureResource(), canonical=True)
api.register(PerNatureByYearResource(), canonical=True)
api.register(PerNatureByMonthResource(), canonical=True)
api.register(PerLegislatorResource(), canonical=True)
api.register(BiggestSupplierForYearResource(), canonical=True)


urlpatterns = api.urls
