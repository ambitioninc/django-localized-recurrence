# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import timezone_field.fields
import localized_recurrence.fields
import datetime


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='LocalizedRecurrence',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, auto_created=True, verbose_name='ID')),
                ('interval', models.CharField(default='DAY', choices=[('DAY', 'Day'), ('WEEK', 'Week'), ('MONTH', 'Month'), ('QUARTER', 'Quarter'), ('YEAR', 'Year')], max_length=18)),
                ('offset', localized_recurrence.fields.DurationField(default=0)),
                ('timezone', timezone_field.fields.TimeZoneField(default='UTC')),
                ('previous_scheduled', models.DateTimeField(default=datetime.datetime(1970, 1, 1, 0, 0))),
                ('next_scheduled', models.DateTimeField(default=datetime.datetime(1970, 1, 1, 0, 0))),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
