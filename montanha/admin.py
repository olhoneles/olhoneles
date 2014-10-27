# -*- coding: utf-8 -*-
#
# Copyright (©) 2013 Gustavo Noronha Silva
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

from django.contrib import admin
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as _
from montanha.models import *


class HasWikipediaListFilter(admin.SimpleListFilter):
    title = _('Has wikipedia')
    parameter_name = 'wikipedia'

    def lookups(self, request, model_admin):
        return (
            ('yes', _('yes')),
            ('no', _('no')),
        )

    def queryset(self, request, queryset):
        if self.value() == 'yes':
            return queryset.filter(wikipedia__isnull=False)
        if self.value() == 'no':
            return queryset.filter(wikipedia__isnull=True)


class PoliticalPartyAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'name', 'show_logo']
    ordering = ['siglum']
    search_fields = ['name']
    list_filter = [HasWikipediaListFilter]

    def show_logo(self, obj):
        if obj.logo:
            return mark_safe('<img src="%s" width="32" />' % obj.logo.url)
    show_logo.allow_tags = True
    show_logo.short_description = 'Logo'


class LegislatorAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'show_picture']
    ordering = ['name']
    search_fields = ['name']

    def show_picture(self, obj):
        if obj.picture:
            return mark_safe('<img src="%s" width="32" />' % obj.picture.url)
    show_picture.allow_tags = True
    show_picture.short_description = _('Picture')


admin.site.register(Legislator, LegislatorAdmin)
admin.site.register(Mandate)
admin.site.register(Supplier)
admin.site.register(ExpenseNature)
admin.site.register(Expense)
admin.site.register(PoliticalParty, PoliticalPartyAdmin)
admin.site.register(Institution)
admin.site.register(Legislature)
