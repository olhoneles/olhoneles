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

from django.conf import settings
from django.db import models
from django.utils.translation import ugettext as _
from easy_thumbnails.fields import ThumbnailerImageField

from montanha.cpf import Cpf
from montanha.cnpj import Cnpj


class PoliticalParty(models.Model):

    class Meta:
        verbose_name = _("Political Party")
        verbose_name_plural = _("Political Parties")

    siglum = models.CharField(max_length=15,
                              verbose_name=_("Siglum"),
                              unique=True)

    name = models.CharField(max_length=2048,
                            verbose_name=_("Full name"),
                            blank=True,
                            null=True)

    logo = ThumbnailerImageField(
        verbose_name=_('Logo'),
        upload_to='political_party',
        blank=True,
        null=True)

    wikipedia = models.URLField(
        verbose_name=_('Wikipedia'),
        blank=True,
        null=True)

    def __unicode__(self):
        return u"%s" % (self.siglum)


class AlternativeLegislatorName(models.Model):
    name = models.CharField(max_length=2048)

    def __unicode__(self):
        return u"%s" % (self.name)


class Legislator(models.Model):

    class Meta:
        verbose_name = _("Legislator")
        verbose_name_plural = _("Legislators")

    name = models.CharField(max_length=2048,
                            verbose_name=_("Full name"))

    alternative_names = models.ManyToManyField('AlternativeLegislatorName')

    picture = ThumbnailerImageField(
        verbose_name=_('Picture'),
        upload_to='legislator',
        blank=True,
        null=True)

    site = models.URLField(
        verbose_name=_('Site'),
        blank=True,
        null=True)

    email = models.EmailField(
        verbose_name=_('Email'),
        blank=True,
        null=True)

    about = models.TextField(
        verbose_name=_('About'),
        blank=True,
        null=True)

    gender = models.CharField(
        verbose_name=_('Gender'),
        choices=(
            ('F', _('Female')),
            ('M', _('Male'))),
        blank=True,
        null=True,
        max_length=1)

    date_of_birth = models.DateField(
        verbose_name=_('Date of Birth'),
        blank=True,
        null=True)

    def __unicode__(self):
        return u"Legislator %s" % (self.name)

    @property
    def party(self):
        return self.mandate_set.order_by("-date_start")[0].party


class Institution(models.Model):

    class Meta:
        verbose_name = _("Institution")
        verbose_name_plural = _("Institutions")

    name = models.CharField(max_length=2048,
                            verbose_name=_("Name"))

    siglum = models.CharField(max_length=10,
                              verbose_name=_("Siglum"),
                              unique=True)

    logo = ThumbnailerImageField(
        verbose_name=_('Logo'),
        upload_to='institution',
        blank=True,
        null=True)

    def __unicode__(self):
        return u"%s" % (self.name)


class Legislature(models.Model):

    class Meta:
        verbose_name = _("Legislature")
        verbose_name_plural = _("Legislatures")

    institution = models.ForeignKey("Institution")

    original_id = models.CharField(blank=True, null=True,
                                   max_length=512,
                                   verbose_name=_("Original ID"))

    date_start = models.DateField(verbose_name=_("Date started"),
                                  help_text=_("""Date in which this legislature started."""))

    date_end = models.DateField(blank=True, null=True,
                                verbose_name=_("Date ended"),
                                help_text=_("""Date in which this legislature ended."""))

    def __unicode__(self):
        return u"%s's legislature starting at %s, ending at %s" % (self.institution.siglum,
                                                                   str(self.date_start),
                                                                   str(self.date_end))


class Mandate(models.Model):

    class Meta:
        verbose_name = _("Mandate")
        verbose_name_plural = _("Mandates")

    original_id = models.TextField(null=True, blank=True)

    legislator = models.ForeignKey("Legislator")

    legislature = models.ForeignKey("Legislature")

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
                                          """mandate."""),
                              blank=True,
                              null=True)

    state = models.CharField(blank=True, null=True,
                             max_length=512,
                             verbose_name=_("State"),
                             help_text=_("""The state where the legislator comes from."""))

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


class CollectionRun(models.Model):

    class Meta:
        verbose_name = _("Collection")
        verbose_name = _("Collections")

    date = models.DateField(verbose_name=_("Collection date"))
    legislature = models.ForeignKey("Legislature")
    committed = models.BooleanField(default=False)

    def __unicode__(self):
        return u"Collection run on %s for %s" % (self.date, unicode(self.legislature))


class AbstractExpense(models.Model):

    class Meta:
        abstract = True

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
                                help_text=_("The total amount spent."),
                                blank=True,
                                null=True)

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


class Expense(AbstractExpense):

    class Meta:
        verbose_name = _("Expense")
        verbose_name_plural = _("Expenses")

    def save(self, *args, **kwargs):
        if settings.expense_locked_for_collection:
            raise RuntimeError("You should not touch Expense while collecting, use ArchivedExpense instead.")
        super(Expense, self).save(*args, **kwargs)


class ArchivedExpense(AbstractExpense):

    class Meta:
        verbose_name = _("Archived expense")
        verbose_name_plural = _("Archived expenses")

    collection_run = models.ForeignKey("CollectionRun")


class Supplier(models.Model):

    class Meta:
        verbose_name = _("Supplier")
        verbose_name_plural = _("Suppliers")

    name = models.CharField(verbose_name=_("Name"), max_length=200)

    identifier = models.CharField(
        max_length=256,
        verbose_name=_("Supplier identifier"))

    date_opened = models.DateField(
        verbose_name=_("Date Opened"),
        blank=True,
        null=True)

    trade_name = models.CharField(
        verbose_name=_("Trade Name"),
        max_length=200,
        blank=True,
        null=True)

    address = models.TextField(
        verbose_name=_("Address"),
        blank=True,
        null=True)

    juridical_nature = models.CharField(
        verbose_name=_("Juridical Nature"),
        max_length=200,
        blank=True,
        null=True)

    status = models.NullBooleanField(
        verbose_name=_("Status"),
        blank=True,
        null=True)

    main_economic_activity = models.CharField(
        verbose_name=_("Main Economic Activity"),
        max_length=200,
        blank=True,
        null=True)

    last_change = models.DateTimeField(
        verbose_name=_('Last Change'),
        auto_now=True,
        blank=True,
        null=True)

    @property
    def identifier_with_mask(self):
        try:
            if len(self.identifier) == 11:
                return Cpf().format(self.identifier)
            elif len(self.identifier) == 14:
                return Cnpj().format(self.identifier)
            else:
                return self.identifier
        except:
            return self.identifier

    @property
    def identifier_label(self):
        if len(self.identifier) == 11:
            return 'CPF'
        elif len(self.identifier) == 14:
            return 'CNPJ'
        else:
            return _('Identifier')

    def __unicode__(self):
        return u"%s (%s)" % (self.name, self.identifier_with_mask)


# Consolidated data models
class PerNature(models.Model):
    institution = models.ForeignKey("Institution")
    legislature = models.ForeignKey("Legislature",
                                    blank=True,
                                    null=True)
    date_start = models.DateField()
    date_end = models.DateField()
    nature = models.ForeignKey("ExpenseNature")
    expensed = models.DecimalField(max_digits=20, decimal_places=2)


class PerNatureByYear(models.Model):
    institution = models.ForeignKey("Institution")
    year = models.IntegerField()
    nature = models.ForeignKey("ExpenseNature")
    expensed = models.DecimalField(max_digits=20, decimal_places=2)


class PerNatureByMonth(models.Model):
    institution = models.ForeignKey("Institution")
    date = models.DateField()
    nature = models.ForeignKey("ExpenseNature")
    expensed = models.DecimalField(max_digits=20, decimal_places=2)


class PerLegislator(models.Model):
    institution = models.ForeignKey("Institution")
    legislature = models.ForeignKey("Legislature",
                                    blank=True,
                                    null=True)
    legislator = models.ForeignKey("Legislator")
    date_start = models.DateField()
    date_end = models.DateField()
    expensed = models.DecimalField(max_digits=20, decimal_places=2)


class BiggestSupplierForYear(models.Model):
    supplier = models.ForeignKey("Supplier")
    year = models.IntegerField()
    expensed = models.DecimalField(max_digits=20, decimal_places=2)
