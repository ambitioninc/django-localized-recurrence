# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Deleting model 'RecurrenceForObject'
        db.delete_table(u'localized_recurrence_recurrenceforobject')


    def backwards(self, orm):
        # Adding model 'RecurrenceForObject'
        db.create_table(u'localized_recurrence_recurrenceforobject', (
            ('previous_scheduled', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime(1970, 1, 1, 0, 0))),
            ('object_id', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('recurrence', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['localized_recurrence.LocalizedRecurrence'])),
            ('next_scheduled', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime(1970, 1, 1, 0, 0))),
            ('content_type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['contenttypes.ContentType'])),
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
        ))
        db.send_create_signal(u'localized_recurrence', ['RecurrenceForObject'])


    models = {
        u'localized_recurrence.localizedrecurrence': {
            'Meta': {'object_name': 'LocalizedRecurrence'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'interval': ('django.db.models.fields.CharField', [], {'default': "'DAY'", 'max_length': '18'}),
            'next_scheduled': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(1970, 1, 1, 0, 0)'}),
            'offset': ('localized_recurrence.fields.DurationField', [], {'default': 'datetime.timedelta(0)'}),
            'previous_scheduled': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(1970, 1, 1, 0, 0)'}),
            'timezone': ('timezone_field.fields.TimeZoneField', [], {'default': "'UTC'"})
        }
    }

    complete_apps = ['localized_recurrence']