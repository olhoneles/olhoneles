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

from django.conf import settings
from tastypie import fields
from tastypie.cache import SimpleCache
from tastypie.throttle import CacheThrottle
from tastypie.resources import ModelResource, ALL

from montanha.models import (
    Supplier, SupplierActivity, SupplierJuridicalNature, PoliticalParty,
    Legislator, AlternativeLegislatorName, Institution, Legislature,
    Mandate, ExpenseNature, Expense, PerNature, PerNatureByYear,
    PerNatureByMonth, PerLegislator, BiggestSupplierForYear
)


class BasicResource(ModelResource):

    class Meta:
        cache = SimpleCache(timeout=settings.RESOURCE_CACHE_TIMEOUT)
        throttle = CacheThrottle(throttle_at=settings.RESOURCE_MAX_REQUESTS)
        allowed_methods = ['get']


class AlternativeLegislatorNameResource(BasicResource):

    class Meta(BasicResource.Meta):
        resource_name = 'alternative-legislator-names'
        queryset = AlternativeLegislatorName.objects.all()
        filtering = {
            'name': ALL,
        }


class LegislatorResource(BasicResource):

    alternative_names = fields.ToManyField(
        AlternativeLegislatorNameResource,
        'alternative_names',
        related_name='alternative_names',
        null=True,
        blank=True,
        full=True,
    )

    class Meta(BasicResource.Meta):
        resource_name = 'legislators'
        queryset = Legislator.objects.all()
        filtering = {
            'name': ALL,
            'gender': ALL,
        }


class PoliticalPartyResource(BasicResource):

    class Meta(BasicResource.Meta):
        resource_name = 'political-parties'
        queryset = PoliticalParty.objects.all()
        filtering = {
            'name': ALL,
            'siglum': ALL,
        }


class SupplierActivityResource(BasicResource):

    class Meta(BasicResource.Meta):
        resource_name = 'main-activities'
        queryset = SupplierActivity.objects.all()
        filtering = {
            'name': ALL,
            'code': ALL,
        }


class JuridicalNatureResource(BasicResource):

    class Meta(BasicResource.Meta):
        resource_name = 'juridical-nature'
        queryset = SupplierJuridicalNature.objects.all()
        filtering = {
            'name': ALL,
            'code': ALL,
        }


class SupplierResource(BasicResource):

    juridical_nature = fields.ForeignKey(
        JuridicalNatureResource,
        'juridical_nature',
        null=True,
        full=True,
    )

    main_activity = fields.ForeignKey(
        SupplierActivityResource,
        'main_activity',
        null=True,
        full=True,
    )

    secondary_activities = fields.ToManyField(
        SupplierActivityResource,
        'secondary_activities',
        related_name='secondary_activities',
        null=True,
        blank=True,
        full=True,
    )

    class Meta(BasicResource.Meta):
        resource_name = 'suppliers'
        queryset = Supplier.objects.all()
        filtering = {
            'identifier': ALL,
            'name': ALL,
        }


class InstitutionResource(BasicResource):

    class Meta(BasicResource.Meta):
        resource_name = 'institutions'
        queryset = Institution.objects.all()
        filtering = {
            'name': ALL,
            'siglum': ALL,
        }


class LegislatureResource(BasicResource):

    class Meta(BasicResource.Meta):
        resource_name = 'legislatures'
        queryset = Legislature.objects.all()
        filtering = {
            'original_id': ALL,
            'date_start': ALL,
            'date_end': ALL,
        }


class MandateResource(BasicResource):

    legislator = fields.ForeignKey(
        LegislatorResource,
        'legislator',
        null=True,
        full=True,
    )

    legislature = fields.ForeignKey(
        LegislatureResource,
        'legislature',
        null=True,
        full=True,
    )

    political_party = fields.ForeignKey(
        PoliticalPartyResource,
        'party',
        null=True,
        full=True,
    )

    class Meta(BasicResource.Meta):
        resource_name = 'mandates'
        queryset = Mandate.objects.all()
        filtering = {
            'date_start': ALL,
            'date_end': ALL,
            'state': ALL,
        }


class ExpenseNatureResource(BasicResource):

    class Meta(BasicResource.Meta):
        resource_name = 'expenses-nature'
        queryset = ExpenseNature.objects.all()
        filtering = {
            'name': ALL,
            'original_id': ALL,
        }


class ExpenseResource(BasicResource):

    nature = fields.ForeignKey(
        ExpenseNatureResource,
        'nature',
        null=True,
        full=True,
    )

    supplier = fields.ForeignKey(
        SupplierResource,
        'supplier',
        null=True,
        full=True,
    )

    mandate = fields.ForeignKey(
        MandateResource,
        'mandate',
        null=True,
        full=True,
    )

    class Meta(BasicResource.Meta):
        resource_name = 'expenses'
        queryset = Expense.objects.all()
        filtering = {
            'number': ALL,
            'date': ALL,
            'original_id': ALL,
        }


class PerNatureResource(BasicResource):

    institution = fields.ForeignKey(
        InstitutionResource,
        'institution',
        null=True,
        full=True,
    )

    nature = fields.ForeignKey(
        ExpenseNatureResource,
        'nature',
        null=True,
        full=True,
    )

    legislature = fields.ForeignKey(
        LegislatureResource,
        'legislature',
        null=True,
        full=True,
    )

    class Meta(BasicResource.Meta):
        resource_name = 'consolidate-per-nature'
        queryset = PerNature.objects.all()
        filtering = {
            'date_start': ALL,
            'date_end': ALL,
        }


class PerNatureByYearResource(BasicResource):

    institution = fields.ForeignKey(
        InstitutionResource,
        'institution',
        null=True,
        full=True,
    )

    nature = fields.ForeignKey(
        ExpenseNatureResource,
        'nature',
        null=True,
        full=True,
    )

    class Meta(BasicResource.Meta):
        resource_name = 'consolidate-per-nature-by-year'
        queryset = PerNatureByYear.objects.all()
        filtering = {
            'year': ALL,
        }


class PerNatureByMonthResource(BasicResource):

    institution = fields.ForeignKey(
        InstitutionResource,
        'institution',
        null=True,
        full=True,
    )

    nature = fields.ForeignKey(
        ExpenseNatureResource,
        'nature',
        null=True,
        full=True,
    )

    class Meta(BasicResource.Meta):
        resource_name = 'consolidate-per-nature-by-month'
        queryset = PerNatureByMonth.objects.all()
        filtering = {
            'date': ALL,
        }


class PerLegislatorResource(BasicResource):

    legislator = fields.ForeignKey(
        LegislatorResource,
        'legislator',
        null=True,
        full=True,
    )

    legislature = fields.ForeignKey(
        LegislatureResource,
        'legislature',
        null=True,
        full=True,
    )

    institution = fields.ForeignKey(
        InstitutionResource,
        'institution',
        null=True,
        full=True,
    )

    class Meta(BasicResource.Meta):
        resource_name = 'consolidate-per-legislator'
        queryset = PerLegislator.objects.all()
        filtering = {
            'date_start': ALL,
            'date_end': ALL,
        }


class BiggestSupplierForYearResource(BasicResource):

    supplier = fields.ForeignKey(
        SupplierResource,
        'supplier',
        null=True,
        full=True,
    )

    class Meta(BasicResource.Meta):
        resource_name = 'consolidate-biggest-supplier-for-year'
        queryset = BiggestSupplierForYear.objects.all()
        filtering = {
            'year': ALL,
        }
