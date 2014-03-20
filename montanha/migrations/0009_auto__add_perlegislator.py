# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'PerLegislator'
        db.create_table(u'montanha_perlegislator', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('institution', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['montanha.Institution'])),
            ('legislature', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['montanha.Legislature'], null=True, blank=True)),
            ('legislator', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['montanha.Legislator'])),
            ('date_start', self.gf('django.db.models.fields.DateField')()),
            ('date_end', self.gf('django.db.models.fields.DateField')()),
            ('expensed', self.gf('django.db.models.fields.DecimalField')(max_digits=10, decimal_places=2)),
        ))
        db.send_create_signal(u'montanha', ['PerLegislator'])


    def backwards(self, orm):
        # Deleting model 'PerLegislator'
        db.delete_table(u'montanha_perlegislator')


    models = {
        u'montanha.archivedexpense': {
            'Meta': {'object_name': 'ArchivedExpense'},
            'collection_run': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['montanha.CollectionRun']"}),
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
        u'montanha.collectionrun': {
            'Meta': {'object_name': 'CollectionRun'},
            'date': ('django.db.models.fields.DateField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'legislature': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['montanha.Legislature']"})
        },
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
            'about': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'date_of_birth': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'null': 'True', 'blank': 'True'}),
            'gender': ('django.db.models.fields.CharField', [], {'max_length': '1', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '2048'}),
            'original_id': ('django.db.models.fields.TextField', [], {}),
            'picture': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'site': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'})
        },
        u'montanha.legislature': {
            'Meta': {'object_name': 'Legislature'},
            'date_end': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'date_start': ('django.db.models.fields.DateField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'institution': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['montanha.Institution']"}),
            'original_id': ('django.db.models.fields.CharField', [], {'max_length': '512', 'null': 'True', 'blank': 'True'})
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
        u'montanha.perlegislator': {
            'Meta': {'object_name': 'PerLegislator'},
            'date_end': ('django.db.models.fields.DateField', [], {}),
            'date_start': ('django.db.models.fields.DateField', [], {}),
            'expensed': ('django.db.models.fields.DecimalField', [], {'max_digits': '10', 'decimal_places': '2'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'institution': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['montanha.Institution']"}),
            'legislator': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['montanha.Legislator']"}),
            'legislature': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['montanha.Legislature']", 'null': 'True', 'blank': 'True'})
        },
        u'montanha.pernature': {
            'Meta': {'object_name': 'PerNature'},
            'date_end': ('django.db.models.fields.DateField', [], {}),
            'date_start': ('django.db.models.fields.DateField', [], {}),
            'expensed': ('django.db.models.fields.DecimalField', [], {'max_digits': '10', 'decimal_places': '2'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'institution': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['montanha.Institution']"}),
            'legislature': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['montanha.Legislature']", 'null': 'True', 'blank': 'True'}),
            'nature': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['montanha.ExpenseNature']"})
        },
        u'montanha.pernaturebymonth': {
            'Meta': {'object_name': 'PerNatureByMonth'},
            'date': ('django.db.models.fields.DateField', [], {}),
            'expensed': ('django.db.models.fields.DecimalField', [], {'max_digits': '10', 'decimal_places': '2'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'institution': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['montanha.Institution']"}),
            'nature': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['montanha.ExpenseNature']"})
        },
        u'montanha.pernaturebyyear': {
            'Meta': {'object_name': 'PerNatureByYear'},
            'expensed': ('django.db.models.fields.DecimalField', [], {'max_digits': '10', 'decimal_places': '2'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'institution': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['montanha.Institution']"}),
            'nature': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['montanha.ExpenseNature']"}),
            'year': ('django.db.models.fields.IntegerField', [], {})
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