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
    def update_schedule(self, time=None):
        """Update the schedule times for all the provided recurrences.

        :type time: :py:class:`datetime.datetime`
        :param time: The time the schedule was checked. If ``None``,
            defaults to ``datetime.utcnow()``.

        In the common case, this can be called without any arguments.

        .. code-block:: python

            >>> past_due = LocalizedRecurrence.objects.filter(
            ...     next_scheduled__lte=datetime.utcnow()
            ... )
            >>> # Do something with past_due recurrences
            >>> past_due.update_schedule()

        The code above will ensure that all the processed recurrences
        are re-scheduled for their next recurrence.
        """
        _update_schedule(self, time=time)


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
    """The information necessary to act on events in users local
    times. Can be instantiated with ``LocalizedRecurrence.objects.create``

    :type interval: str
    :param interval: The interval at which the event recurs.
        One of ``'DAY'``, ``'WEEK'``, ``'MONTH'``.

    :type offset: :py:class:`datetime.timedelta`
    :param offset: The amount of time into the interval that the event
        occurs at.

    :type timezone: pytz.timezone
    :param timezone: The local timezone for the user.

    Localized recurrences are simply objects in the database. They can
    be created with standard django ORM tools:

    .. code-block:: python

        >>> from datetime import datetime, timedelta
        >>> my_lr = LocalizedRecurrence.objects.create(
        ...     interval='DAY',
        ...     offset=timedela(hours=15),
        ...     timezone=pytz.timedelta('US/Eastern'),
        ... )

    Once instantiated it is simple to check if a localized recurrence
    is due to be acted upon.

    .. code-block:: python

        >>> my_lr.next_scheduled < datetime.utcnow()
        True

    After a recurrence has been acted upon, it's schedule can be
    simply reset to occur at the prescribed time in the next interval.

    .. code-block:: python

        >>> my_lr.update_schedule()
        >>> my_lr.next_scheduled < datetime.utcnow()
        False

    """
    interval = models.CharField(max_length=18, default='DAY', choices=INTERVAL_CHOICES)
    offset = DurationField(default=timedelta(0))
    timezone = TimeZoneField(default='UTC')
    previous_scheduled = models.DateTimeField(default=datetime(1970, 1, 1))
    next_scheduled = models.DateTimeField(default=datetime(1970, 1, 1))

    objects = LocalizedRecurrenceManager()

    def check_due(self, objects, time=None):
        """Return all the objects that are past due.

        This function is used to track a number of objects using a
        single localized recurrence. An object stored in the database
        can be tracked.

        :type objects: list of model instances
        :param objects: This list of objects all recur on the same
            frequency, but may not have been acted upon yet.

        :type time: :py:class:`datetime.datetime`
        :param time: Check if the objects are due at this time. If
            ``None`` defaults to ``datetime.utcnow()``.

        :rtype: list of model instance
        :returns: The list of objects passed in, filtered such that
            only those objects that are due (their next scheduled time
            is before the given ``time``) are included.

        If an object has not been checked before, it will
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
                self._sub_recurrence(obj)
        return due

    def _sub_recurrence(self, for_object):
        """Return the :class:`.RecurrenceForObject` of the given object.
        """
        ct = ContentType.objects.get_for_model(for_object)
        sub, created = RecurrenceForObject.objects.get_or_create(
            recurrence=self,
            content_type=ct,
            object_id=for_object.id
        )
        return sub

    def update_schedule(self, time=None, for_object=None):
        """Update the schedule for this recurrence or an object it tracks.

        :type time: :py:class:`datetime.datetime`
        :param time: The time the schedule was checked. If ``None``,
            defaults to ``datetime.utcnow()``.

        :type for_object: django model instance
        :param for_object: Optional. Update the schedule for the
            given object on the recurrence, rather than the the
            schedule of the recurrence itself.
        """
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
