# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from datetime import timedelta
from django.db import migrations


def migrate_integers_to_intervals(apps, schema_editor):
    # Migrate custom DurationField values to Django's Native DurationField values
    LocalizedRecurrence = apps.get_model('localized_recurrence', 'LocalizedRecurrence')
    for lr in LocalizedRecurrence.objects.all():
        lr.offset2 = lr.offset
        lr.save()


class Migration(migrations.Migration):
    dependencies = [
        ('localized_recurrence', '0002_localizedrecurrence_offset2'),
    ]

    operations = [
        migrations.RunPython(migrate_integers_to_intervals),
    ]
