# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'LocalizedRecurrence'
        db.create_table(u'localized_recurrence_localizedrecurrence', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('interval', self.gf('django.db.models.fields.CharField')(default='DAY', max_length=18)),
            ('offset', self.gf('localized_recurrence.fields.DurationField')(default=datetime.timedelta(0))),
            ('timezone', self.gf('timezone_field.fields.TimeZoneField')(default='UTC')),
            ('previous_scheduled', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime(1970, 1, 1, 0, 0))),
            ('next_scheduled', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime(1970, 1, 1, 0, 0))),
        ))
        db.send_create_signal(u'localized_recurrence', ['LocalizedRecurrence'])

        # Adding model 'RecurrenceForObject'
        db.create_table(u'localized_recurrence_recurrenceforobject', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('recurrence', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['localized_recurrence.LocalizedRecurrence'])),
            ('content_type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['contenttypes.ContentType'])),
            ('object_id', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('previous_scheduled', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime(1970, 1, 1, 0, 0))),
            ('next_scheduled', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime(1970, 1, 1, 0, 0))),
        ))
        db.send_create_signal(u'localized_recurrence', ['RecurrenceForObject'])


    def backwards(self, orm):
        # Deleting model 'LocalizedRecurrence'
        db.delete_table(u'localized_recurrence_localizedrecurrence')

        # Deleting model 'RecurrenceForObject'
        db.delete_table(u'localized_recurrence_recurrenceforobject')


    models = {
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'localized_recurrence.localizedrecurrence': {
            'Meta': {'object_name': 'LocalizedRecurrence'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'interval': ('django.db.models.fields.CharField', [], {'default': "'DAY'", 'max_length': '18'}),
            'next_scheduled': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(1970, 1, 1, 0, 0)'}),
            'offset': ('localized_recurrence.fields.DurationField', [], {'default': 'datetime.timedelta(0)'}),
            'previous_scheduled': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(1970, 1, 1, 0, 0)'}),
            'timezone': ('timezone_field.fields.TimeZoneField', [], {'default': "'UTC'"})
        },
        u'localized_recurrence.recurrenceforobject': {
            'Meta': {'object_name': 'RecurrenceForObject'},
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'next_scheduled': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(1970, 1, 1, 0, 0)'}),
            'object_id': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'previous_scheduled': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(1970, 1, 1, 0, 0)'}),
            'recurrence': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['localized_recurrence.LocalizedRecurrence']"})
        }
    }

    complete_apps = ['localized_recurrence']