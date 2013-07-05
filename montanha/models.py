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

from django.db import models
from django.utils.translation import ugettext as _


class PoliticalParty(models.Model):

    class Meta:
        verbose_name = _("Political Party")
        verbose_name_plural = _("Political Parties")

    siglum = models.CharField(max_length=10,
                              verbose_name=_("Siglum"),
                              unique=True)

    name = models.CharField(max_length=2048,
                            verbose_name=_("Full name"))

    def __unicode__(self):
        return u"%s" % (self.siglum)


class Legislator(models.Model):

    class Meta:
        verbose_name = _("Legislator")
        verbose_name_plural = _("Legislators")

    original_id = models.TextField()

    name = models.CharField(max_length=2048,
                            verbose_name=_("Full name"))

    def __unicode__(self):
        if self.original_id:
            return u"Legislator %s (Original ID: %s)" % (self.name, self.original_id)

        return u"Legislator %s" % (self.name)


class Institution(models.Model):

    class Meta:
        verbose_name = _("Institution")
        verbose_name_plural = _("Institutions")

    name = models.CharField(max_length=2048,
                            verbose_name=_("Name"))


class Mandate(models.Model):

    class Meta:
        verbose_name = _("Mandate")
        verbose_name_plural = _("Mandates")

    legislator = models.ForeignKey("Legislator")

    institution = models.ForeignKey("Institution")

    date_start = models.DateField(verbose_name=_("Date started"),
                                  help_text=_("""Date in which this mandate started; may also be """
                                              """a resumption of a mandate that was paused for taking """
                                              """an executive-branch office, or a party change."""))

    date_end = models.DateField(blank=True, null=True,
                                verbose_name=_("Date ended"),
                                help_text=_("""Date in which this mandate ended, paused for taking an """
                                            """executive-branch office, or affiliation change."""))

    party = models.ForeignKey("PoliticalParty",
                              verbose_name=_("Party"),
                              help_text=_("""Party the legislator was affiliated to during this """
                                          """mandate."""))

    def __unicode__(self):
        if self.date_end:
            return u"%s's ongoing mandate started on %s, affiliated with %s" % (self.legislator.name,
                                                                                str(self.date_start),
                                                                                self.party)

        return u"%s's mandate started on %s ended on %s, affiliated with %s" % (self.legislator.name,
                                                                                str(self.date_start),
                                                                                str(self.date_end),
                                                                                self.party)


class ExpenseNature(models.Model):

    class Meta:
        verbose_name = _("Expense nature")
        verbose_name_plural = _("Expense natures")

    original_id = models.CharField(blank=True, null=True,
                                   max_length=512,
                                   verbose_name=_("Original ID"))

    name = models.CharField(max_length=512,
                            verbose_name=_("Expense nature name"))

    def __unicode__(self):
        return u"%s" % self.name


class Expense(models.Model):

    class Meta:
        verbose_name = _("Expense")
        verbose_name_plural = _("Expenses")

    original_id = models.CharField(blank=True, null=True,
                                   max_length=512,
                                   verbose_name=_("Original ID"))

    number = models.CharField(max_length=512,
                              verbose_name=_("Document number"),
                              help_text=_("Usually a receipt ID."))

    nature = models.ForeignKey('ExpenseNature')

    date = models.DateField(verbose_name=_("Expense date"))

    value = models.DecimalField(max_digits=10,
                                decimal_places=2,
                                verbose_name=_("Value"),
                                help_text=_("The total amount spent."))

    expensed = models.DecimalField(max_digits=10, decimal_places=2,
                                   verbose_name=_("Expensed"),
                                   help_text=_("Amount reimbursed to the legislator."))

    mandate = models.ForeignKey("Mandate")

    supplier = models.ForeignKey("Supplier")

    def __unicode__(self):
        return u"%s expensed by %s on %s (document %s)" % (str(self.expensed),
                                                           self.mandate.legislator.name,
                                                           str(self.date),
                                                           self.number)


class Supplier(models.Model):

    class Meta:
        verbose_name = _("Supplier")
        verbose_name_plural = _("Suppliers")

    identifier = models.CharField(max_length=256,
                                  verbose_name=_("Supplier identifier"))

    name = models.CharField(max_length=200)

    def __unicode__(self):
        return u"%s (%s)" % (self.name, self.identifier)
