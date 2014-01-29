# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import DataMigration
from django.db import models

class Migration(DataMigration):

    def forwards(self, orm):
        for legislature in orm.Legislature.objects.all():
            collection_run = orm.CollectionRun(legislature=legislature,
                                               date=datetime.date.today())
            collection_run.save()

            for expense in orm.Expense.objects.filter(mandate__legislature=legislature).all():
                exp = orm.ArchivedExpense(original_id=expense.original_id,
                                          number=expense.number,
                                          nature=expense.nature,
                                          date=expense.date,
                                          value=expense.value,
                                          expensed=expense.expensed,
                                          mandate=expense.mandate,
                                          supplier=expense.supplier,
                                          collection_run=collection_run)
                exp.save()

                try:
                    e = orm.Expense.objects.get(original_id=expense.original_id,
                                                number=expense.number,
                                                nature=expense.nature,
                                                date=expense.date,
                                                value=expense.value,
                                                expensed=expense.expensed,
                                                mandate=expense.mandate,
                                                supplier=expense.supplier)
                except Exception, e:
                    import pdb;pdb.set_trace()

    def backwards(self, orm):
        raise RuntimeError("No can do.")

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
    symmetrical = True
