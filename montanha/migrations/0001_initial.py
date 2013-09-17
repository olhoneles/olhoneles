# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'PoliticalParty'
        db.create_table(u'montanha_politicalparty', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('siglum', self.gf('django.db.models.fields.CharField')(unique=True, max_length=10)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=2048, null=True, blank=True)),
            ('logo', self.gf('django.db.models.fields.files.ImageField')(max_length=100, null=True, blank=True)),
            ('wikipedia', self.gf('django.db.models.fields.URLField')(max_length=200, null=True, blank=True)),
        ))
        db.send_create_signal(u'montanha', ['PoliticalParty'])

        # Adding model 'Legislator'
        db.create_table(u'montanha_legislator', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('original_id', self.gf('django.db.models.fields.TextField')()),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=2048)),
            ('picture', self.gf('django.db.models.fields.files.ImageField')(max_length=100, null=True, blank=True)),
        ))
        db.send_create_signal(u'montanha', ['Legislator'])

        # Adding model 'Institution'
        db.create_table(u'montanha_institution', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=2048)),
            ('siglum', self.gf('django.db.models.fields.CharField')(unique=True, max_length=10)),
            ('logo', self.gf('django.db.models.fields.files.ImageField')(max_length=100, null=True, blank=True)),
        ))
        db.send_create_signal(u'montanha', ['Institution'])

        # Adding model 'Legislature'
        db.create_table(u'montanha_legislature', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('institution', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['montanha.Institution'])),
            ('date_start', self.gf('django.db.models.fields.DateField')()),
            ('date_end', self.gf('django.db.models.fields.DateField')(null=True, blank=True)),
        ))
        db.send_create_signal(u'montanha', ['Legislature'])

        # Adding model 'Mandate'
        db.create_table(u'montanha_mandate', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('legislator', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['montanha.Legislator'])),
            ('legislature', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['montanha.Legislature'])),
            ('date_start', self.gf('django.db.models.fields.DateField')()),
            ('date_end', self.gf('django.db.models.fields.DateField')(null=True, blank=True)),
            ('party', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['montanha.PoliticalParty'], null=True, blank=True)),
        ))
        db.send_create_signal(u'montanha', ['Mandate'])

        # Adding model 'ExpenseNature'
        db.create_table(u'montanha_expensenature', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('original_id', self.gf('django.db.models.fields.CharField')(max_length=512, null=True, blank=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=512)),
        ))
        db.send_create_signal(u'montanha', ['ExpenseNature'])

        # Adding model 'Expense'
        db.create_table(u'montanha_expense', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('original_id', self.gf('django.db.models.fields.CharField')(max_length=512, null=True, blank=True)),
            ('number', self.gf('django.db.models.fields.CharField')(max_length=512)),
            ('nature', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['montanha.ExpenseNature'])),
            ('date', self.gf('django.db.models.fields.DateField')()),
            ('value', self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=10, decimal_places=2, blank=True)),
            ('expensed', self.gf('django.db.models.fields.DecimalField')(max_digits=10, decimal_places=2)),
            ('mandate', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['montanha.Mandate'])),
            ('supplier', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['montanha.Supplier'])),
        ))
        db.send_create_signal(u'montanha', ['Expense'])

        # Adding model 'Supplier'
        db.create_table(u'montanha_supplier', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('identifier', self.gf('django.db.models.fields.CharField')(max_length=256)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=200)),
        ))
        db.send_create_signal(u'montanha', ['Supplier'])


    def backwards(self, orm):
        # Deleting model 'PoliticalParty'
        db.delete_table(u'montanha_politicalparty')

        # Deleting model 'Legislator'
        db.delete_table(u'montanha_legislator')

        # Deleting model 'Institution'
        db.delete_table(u'montanha_institution')

        # Deleting model 'Legislature'
        db.delete_table(u'montanha_legislature')

        # Deleting model 'Mandate'
        db.delete_table(u'montanha_mandate')

        # Deleting model 'ExpenseNature'
        db.delete_table(u'montanha_expensenature')

        # Deleting model 'Expense'
        db.delete_table(u'montanha_expense')

        # Deleting model 'Supplier'
        db.delete_table(u'montanha_supplier')


    models = {
        u'montanha.expense': {
            'Meta': {'object_name': 'Expense'},
            'date': ('django.db.models.fields.DateField', [], {}),
            'expensed': ('django.db.models.fields.DecimalField', [], {'max_digits': '10', 'decimal_places': '2'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'mandate': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['montanha.Mandate']"}),
            'nature': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['montanha.ExpenseNature']"}),
            'number': ('django.db.models.fields.CharField', [], {'max_length': '512'}),
            'original_id': ('django.db.models.fields.CharField', [], {'max_length': '512', 'null': 'True', 'blank': 'True'}),
            'supplier': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['montanha.Supplier']"}),
            'value': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '10', 'decimal_places': '2', 'blank': 'True'})
        },
        u'montanha.expensenature': {
            'Meta': {'object_name': 'ExpenseNature'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '512'}),
            'original_id': ('django.db.models.fields.CharField', [], {'max_length': '512', 'null': 'True', 'blank': 'True'})
        },
        u'montanha.institution': {
            'Meta': {'object_name': 'Institution'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'logo': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '2048'}),
            'siglum': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '10'})
        },
        u'montanha.legislator': {
            'Meta': {'object_name': 'Legislator'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '2048'}),
            'original_id': ('django.db.models.fields.TextField', [], {}),
            'picture': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'})
        },
        u'montanha.legislature': {
            'Meta': {'object_name': 'Legislature'},
            'date_end': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'date_start': ('django.db.models.fields.DateField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'institution': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['montanha.Institution']"})
        },
        u'montanha.mandate': {
            'Meta': {'object_name': 'Mandate'},
            'date_end': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'date_start': ('django.db.models.fields.DateField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'legislator': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['montanha.Legislator']"}),
            'legislature': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['montanha.Legislature']"}),
            'party': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['montanha.PoliticalParty']", 'null': 'True', 'blank': 'True'})
        },
        u'montanha.politicalparty': {
            'Meta': {'object_name': 'PoliticalParty'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'logo': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '2048', 'null': 'True', 'blank': 'True'}),
            'siglum': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '10'}),
            'wikipedia': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'})
        },
        u'montanha.supplier': {
            'Meta': {'object_name': 'Supplier'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'identifier': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'})
        }
    }

    complete_apps = ['montanha']