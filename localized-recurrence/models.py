from datetime import datetime, timedelta

from dateutil.relativedelta import relativedelta
from django.db import models
from timezone_field import TimeZoneField
import fleming
import pytz

from .fields import DurationField


INTERVAL_CHOICES = (
    ('DAY', 'Day'),
    ('WEEK', 'Week'),
    ('MONTH', 'Month')
)


class LocalizedRecurrenceQuerySet(models.query.QuerySet):
    def update_schedule(self, time=None):
        """Update the schedule times for all the recurrences in the queryset.
        """
        time = time or datetime.utcnow()
        for recurrence in self:
            recurrence.next_scheduled = recurrence.utc_of_next_schedule(time)
            recurrence.previous_scheduled = time
            recurrence.save()


class LocalizedRecurrenceManager(models.Manager):
    def get_queryset(self):
        return LocalizedRecurrenceQuerySet(self.model)

    def __getattr__(self, name):
        """
        Written to allow both:
            - LocalizedRecurrence.objects.update_schedule()
            - LocalizedRecurrence.get(id=my_recurrence).update_schedule()
        """
        return getattr(self.get_queryset(), name)


class LocalizedRecurrence(models.Model):
    """The information necessary to act on events in users local times.
    """
    interval = models.CharField(max_length=18, default='DAY', choices=INTERVAL_CHOICES)
    offset = DurationField(default=timedelta(0))
    timezone = TimeZoneField(default='UTC')
    previous_scheduled = models.DateTimeField(default=datetime(1970, 1, 1))
    next_scheduled = models.DateTimeField(default=datetime(1970, 1, 1))

    objects = LocalizedRecurrenceManager()

    def utc_of_next_schedule(self, current_time):
        local_time = fleming.convert_to_tz(current_time, self.timezone)
        local_scheduled_time = replace_with_offset(local_time, self.offset, self.interval)
        utc_scheduled_time = fleming.convert_to_tz(local_scheduled_time, pytz.utc, return_naive=True)
        if utc_scheduled_time <= current_time:
            additional_time = {
                'DAY': timedelta(days=1),
                'WEEK': timedelta(weeks=1),
                'MONTH': relativedelta(months=1)
            }
            utc_scheduled_time = fleming.add_timedelta(
                utc_scheduled_time, additional_time[self.interval], within_tz=self.timezone)
        return utc_scheduled_time


def replace_with_offset(dt, offset, interval):
    """Replace components of a datetime with those of a timedelta.

    This replacement is done within the given interval. This means the
    the final result, will the be a datetime, at the desired offset
    given the interval.
    """
    hours, minutes, seconds = offset.seconds // 3600, (offset.seconds // 60) % 60, offset.seconds % 60
    interval = interval.lower()
    if interval == 'day':
        dt_out = dt.replace(hour=hours, minute=minutes, second=seconds)
    elif interval == 'week':
        dt_out = dt + timedelta(days=offset.days - dt.weekday())
        dt_out = dt_out.replace(hour=hours, minute=minutes, second=seconds)
    elif interval == 'month':
        # TODO:
        #     - Modify so it works with the last day of the month
        #     - As per: http://stackoverflow.com/questions/42950/get-last-day-of-the-month-in-python
        #     - Add test for: e.g. February 30th.
        dt_out = dt.replace(day=offset.days + 1, hour=hours, minute=minutes, second=seconds)
    else:
        raise ValueError('{i} is not a proper interval value'.format(i=interval))
    return dt_out
