from datetime import datetime, timedelta

from dateutil.relativedelta import relativedelta
from django.contrib.contenttypes import generic
from django.contrib.contenttypes.models import ContentType
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
    def update_schedule(self, time=None, for_object=None):
        _update_schedule(self, time=time, for_object=for_object)


class LocalizedRecurrenceManager(models.Manager):
    def get_queryset(self):
        return LocalizedRecurrenceQuerySet(self.model)

    def __getattr__(self, name):
        """
        Written to allow both:
            - LocalizedRecurrence.objects.update_schedule()
            - LocalizedRecurrence.filter(id=my_recurrence.id).update_schedule()
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

    def check_due(self, objects, time=None):
        """Return all the objects that are past due.

        Args:
          objects - a list of objects to check if they are due.
          time (optional) - a time

        Side Effect:

          Any objects creates a RecurrenceForObject for each object in
          the `objects` argument missing.

        Returns

          A list of all the objects from the `objects` argument where
          their `next_scheduled` is less than the `time` arguement (or
          utcnow()). Objects that were not previously tracked will
          automatically be returned.
        """
        time = time or datetime.utcnow()
        recurrences = self.recurrenceforobject_set.prefetch_related('content_object').all()
        all_scheduled_objs = set(r.content_object for r in recurrences)
        past_due = set(r.content_object for r in recurrences.filter(next_scheduled__lt=time))

        due = []
        for obj in objects:
            if obj in all_scheduled_objs and obj in past_due:
                due.append(obj)
            elif obj not in all_scheduled_objs:
                due.append(obj)
                self.sub_recurrence(obj)
        return due

    def sub_recurrence(self, for_object):
        """Return the sub_recurrence for the given object.
        """
        ct = ContentType.objects.get_for_model(for_object)
        sub, created = RecurrenceForObject.objects.get_or_create(
            recurrence=self,
            content_type=ct,
            object_id=for_object.id
        )
        return sub

    def update_schedule(self, time=None, for_object=None):
        _update_schedule([self], time, for_object)

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


class RecurrenceForObject(models.Model):
    """Updates to a recurrence for different objects.
    """
    recurrence = models.ForeignKey('LocalizedRecurrence')
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    content_object = generic.GenericForeignKey('content_type', 'object_id')
    previous_scheduled = models.DateTimeField(default=datetime(1970, 1, 1))
    next_scheduled = models.DateTimeField(default=datetime(1970, 1, 1))


def _update_schedule(recurrences, time=None, for_object=None):
        """Update the schedule times for all the provided recurrences.

        Args:
          recurrences - an iterable of LocalizedRecurrence objects to
          update (either directly, or their component objects)

          time - The time the schedule was checked. If None, defaults
          to utcnow.

          for_object - Any instance of a django model. Allows a single
          recurrence to be updated for multiple
          users/entities/objects/etc.

        Side Effects:
          If `for_object` is None, updates the `next_scheduled` and
          `previous_scheduled` fields for every recurrence in the
          iterable.

          If `for_object` is not None, creates or updates the
          `next_scheduled` and `previous_scheduled` fields on a
          `RecurrenceForObject` instance associated with each
          recurrence in the iterable.

        """
        time = time or datetime.utcnow()
        if for_object is None:
            for recurrence in recurrences:
                recurrence.next_scheduled = recurrence.utc_of_next_schedule(time)
                recurrence.previous_scheduled = time
                recurrence.save()
        else:
            for recurrence in recurrences:
                ct = ContentType.objects.get_for_model(for_object)
                obj, created = RecurrenceForObject.objects.get_or_create(
                    recurrence=recurrence,
                    content_type=ct,
                    object_id=for_object.id
                )
                obj.next_scheduled = recurrence.utc_of_next_schedule(time)
                obj.previous_scheduled = time
                obj.save()


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
