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
from localflavor.br.br_states import STATE_CHOICES
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
        max_length=256,
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
        party = self.mandate_set.order_by("-date_start")[0].party
        if party and party.siglum:
            return party.siglum
        return u"Partido não informado"


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
                                  help_text=_("""Date in which this legislature started."""),
                                  db_index=True)

    date_end = models.DateField(blank=True, null=True,
                                verbose_name=_("Date ended"),
                                help_text=_("""Date in which this legislature ended."""),
                                db_index=True)

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
                                              """an executive-branch office, or a party change."""),
                                  db_index=True)

    date_end = models.DateField(blank=True, null=True,
                                verbose_name=_("Date ended"),
                                help_text=_("""Date in which this mandate ended, paused for taking an """
                                            """executive-branch office, or affiliation change."""),
                                db_index=True)

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

    date = models.DateField(verbose_name=_("Collection date"), db_index=True)
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

    date = models.DateField(verbose_name=_("Expense date"), db_index=True)

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
        if hasattr(settings, 'expense_locked_for_collection') and \
           settings.expense_locked_for_collection:
            raise RuntimeError("You should not touch Expense while collecting, use ArchivedExpense instead.")
        super(Expense, self).save(*args, **kwargs)


class ArchivedExpense(AbstractExpense):

    class Meta:
        verbose_name = _("Archived expense")
        verbose_name_plural = _("Archived expenses")

    collection_run = models.ForeignKey("CollectionRun")


class SupplierActivity(models.Model):

    class Meta:
        verbose_name = _('Supplier Activity')
        verbose_name_plural = _('Supplier Activities')

    name = models.CharField(max_length=248, verbose_name=_('Name'))

    code = models.CharField(max_length=10, verbose_name=_('Code'), unique=True)

    def __unicode__(self):
        return u'{0} ({1})'.format(self.name, self.code)


class SupplierJuridicalNature(models.Model):

    class Meta:
        verbose_name = _('Supplier Juridical Nature')
        verbose_name_plural = _('Supplier Juridical Nature')

    name = models.CharField(max_length=248, verbose_name=_('Name'))

    code = models.CharField(max_length=10, verbose_name=_('Code'), unique=True)

    def __unicode__(self):
        return u'{0} ({1})'.format(self.name, self.code)


class SupplierSituation(models.Model):

    class Meta:
        verbose_name = _('Supplier Situation')
        verbose_name_plural = _('Supplier Situations')

    name = models.CharField(verbose_name=_('Name'), max_length=200)

    def __unicode__(self):
        return u'{0}'.format(self.name)


class Supplier(models.Model):

    class Meta:
        verbose_name = _("Supplier")
        verbose_name_plural = _("Suppliers")

    name = models.CharField(verbose_name=_("Name"), max_length=200)

    identifier = models.CharField(
        max_length=256,
        verbose_name=_("Supplier identifier"),
        db_index=True)

    date_opened = models.DateField(
        verbose_name=_("Date Opened"),
        blank=True,
        null=True)

    trade_name = models.CharField(
        verbose_name=_("Trade Name"),
        max_length=200,
        blank=True,
        null=True)

    status = models.CharField(
        verbose_name=_('Status'),
        max_length=10,
        blank=True,
        null=True)

    situation = models.ForeignKey(
        'SupplierSituation',
        verbose_name=_('Situation'),
        blank=True,
        null=True,
    )

    situation_date = models.DateField(
        verbose_name=_('Situation Date'),
        blank=True,
        null=True,
    )

    situation_reason = models.CharField(
        verbose_name=_('Situation Reason'),
        max_length=200,
        blank=True,
        null=True,
    )

    special_situation = models.CharField(
        verbose_name=_('Special Situation'),
        max_length=200,
        blank=True,
        null=True,
    )

    special_situation_date = models.DateField(
        verbose_name=_('Special Situation Date'),
        blank=True,
        null=True,
    )

    enterprise_type = models.CharField(
        verbose_name=_('Enterprise Type'),
        max_length=6,
        blank=True,
        null=True,
    )

    federative_officer = models.CharField(
        verbose_name=_('Federative Officer'),
        max_length=200,
        blank=True,
        null=True,
    )

    last_change = models.DateTimeField(
        verbose_name=_('Last Change'),
        auto_now=True,
        blank=True,
        null=True,
    )

    last_update = models.DateTimeField(
        verbose_name=_('Last Update'),
        blank=True,
        null=True,
    )

    email = models.EmailField(
        verbose_name=_('Email'),
        blank=True,
        null=True,
    )

    juridical_nature = models.ForeignKey(
        'SupplierJuridicalNature',
        verbose_name=_('Juridical Nature'),
        blank=True,
        null=True,
    )

    address = models.CharField(
        verbose_name=_('Address'),
        max_length=200,
        blank=True,
        null=True,
    )

    address_number = models.CharField(
        verbose_name=_('Address Number'),
        max_length=10,
        null=True,
        blank=True,
    )

    address_complement = models.CharField(
        verbose_name=_('Address Complement'),
        max_length=200,
        blank=True,
        null=True,
    )

    postal_code = models.CharField(
        verbose_name=_('CEP'),
        max_length=100,
        blank=True,
        null=True,
    )

    state = models.CharField(
        verbose_name=_('State'),
        max_length=2,
        choices=STATE_CHOICES,
        blank=True,
        null=True,
    )

    city = models.CharField(
        verbose_name=_('City'),
        max_length=100,
        blank=True,
        null=True,
    )

    neighborhood = models.CharField(
        verbose_name=_('Neighborhood'),
        max_length=100,
        blank=True,
        null=True,
    )

    phone = models.CharField(
        verbose_name=_('Phone'),
        max_length=100,
        blank=True,
        null=True,
    )

    main_activity = models.ForeignKey(
        'SupplierActivity',
        verbose_name=_('Main Activity'),
        blank=True,
        null=True,
    )

    secondary_activities = models.ManyToManyField(
        'SupplierActivity',
        verbose_name=_('Secondary Activities'),
        related_name='secondary_activities',
        blank=True,
    )

    @property
    def identifier_with_mask(self):
        try:
            if len(self.identifier) == 11:
                return Cpf().format(self.identifier)
            elif len(self.identifier) == 14:
                return Cnpj().format(self.identifier)
            else:
                return self.identifier
        except Exception:
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
    date_start = models.DateField(db_index=True)
    date_end = models.DateField(db_index=True)
    nature = models.ForeignKey("ExpenseNature")
    expensed = models.DecimalField(max_digits=20, decimal_places=2)

    class Meta:
        verbose_name = _("Per Nature")
        verbose_name_plural = _("Per Nature")

    def __unicode__(self):
        return u'{0} ({1})'.format(self.nature, self.expensed)


class PerNatureByYear(models.Model):
    institution = models.ForeignKey("Institution")
    year = models.IntegerField()
    nature = models.ForeignKey("ExpenseNature")
    expensed = models.DecimalField(max_digits=20, decimal_places=2)

    class Meta:
        verbose_name = _("Per Nature By Year")
        verbose_name_plural = _("Per Nature By Year")

    def __unicode__(self):
        return u'{0} ({1})'.format(self.nature, self.expensed)


class PerNatureByMonth(models.Model):
    institution = models.ForeignKey("Institution")
    date = models.DateField(db_index=True)
    nature = models.ForeignKey("ExpenseNature")
    expensed = models.DecimalField(max_digits=20, decimal_places=2)

    class Meta:
        verbose_name = _("Per Nature By Month")
        verbose_name_plural = _("Per Nature By Month")

    def __unicode__(self):
        return u'{0} ({1})'.format(self.nature, self.expensed)


class PerLegislator(models.Model):
    institution = models.ForeignKey("Institution")
    legislature = models.ForeignKey("Legislature",
                                    blank=True,
                                    null=True)
    legislator = models.ForeignKey("Legislator")
    date_start = models.DateField(db_index=True)
    date_end = models.DateField(db_index=True)
    expensed = models.DecimalField(max_digits=20, decimal_places=2)

    class Meta:
        verbose_name = _("Per Legislator")
        verbose_name_plural = _("Per Legislator")

    def __unicode__(self):
        return u'{0} ({1})'.format(self.legislator, self.expensed)


class BiggestSupplierForYear(models.Model):
    supplier = models.ForeignKey("Supplier")
    year = models.IntegerField(db_index=True)
    expensed = models.DecimalField(max_digits=20, decimal_places=2)

    class Meta:
        verbose_name = _("Biggest Supplier For Year")
        verbose_name_plural = _("Biggest Supplier For Year")

    def __unicode__(self):
        return u'{0} ({1})'.format(self.supplier, self.expensed)
