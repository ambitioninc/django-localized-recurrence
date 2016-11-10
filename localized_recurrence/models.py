from datetime import datetime, timedelta
import calendar

from dateutil.relativedelta import relativedelta
from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from timezone_field import TimeZoneField
import fleming
import pytz


INTERVAL_CHOICES = (
    ('DAY', 'Day'),
    ('WEEK', 'Week'),
    ('MONTH', 'Month'),
    ('QUARTER', 'Quarter'),
    ('YEAR', 'Year'),
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

        Calling this function has the side effect that the
        ``next_scheduled`` attribute of every recurrence in the
        queryset will be updated to the new time in utc.
        """
        _update_schedule(self, time=time)


class LocalizedRecurrenceManager(models.Manager):
    def get_queryset(self):
        return LocalizedRecurrenceQuerySet(self.model)

    def update_schedule(self, time=None):
        """Update the schedule times for all recurrences.

        Functions exactly the same as the method on the querysets. The
        following to calls are equivalent:

        .. code-block:: python

            >>> LocalizedRecurrence.objects.all().update_schedule()
            >>> LocalizedRecurrence.objects.update_schedule()

        Calling this function has the side effect that the
        ``next_scheduled`` attribute of every recurrence will be
        updated to the new time in utc.
        """
        self.get_queryset().update_schedule(time=time)


@python_2_unicode_compatible
class LocalizedRecurrence(models.Model):
    """The information necessary to act on events in users local
    times. Can be instantiated with ``LocalizedRecurrence.objects.create``

    :type interval: str
    :param interval: The interval at which the event recurs.
        One of ``'DAY'``, ``'WEEK'``, ``'MONTH'``, ``'QUARTER'``, ``'YEAR'``.

    :type offset: :py:class:`datetime.timedelta`
    :param offset: The amount of time into the interval that the event
        occurs at.

        If the interval is monthly, quarterly, or yearly, the number
        of days in the interval are variable. In the case of offsets
        with more days than the number of days in the interval,
        updating the schedule will not raise an error, but will update
        to the last day in the interval if necessary.

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
    offset = models.DurationField(default=timedelta(0))
    timezone = TimeZoneField(default='UTC')
    previous_scheduled = models.DateTimeField(default=datetime(1970, 1, 1))
    next_scheduled = models.DateTimeField(default=datetime(1970, 1, 1))

    objects = LocalizedRecurrenceManager()

    def __str__(self):
        return 'ID: {0}, Interval: {1}, Next Scheduled: {2}'.format(self.id, self.interval, self.next_scheduled)

    def update(self, **updates):
        """Updates fields in the localized recurrence."""
        for update in updates:
            setattr(self, update, updates[update])

        return self.save()

    def update_schedule(self, time=None):
        """Update the schedule for this recurrence or an object it tracks.

        :type time: :py:class:`datetime.datetime`
        :param time: The time the schedule was checked. If ``None``,
            defaults to ``datetime.utcnow()``.

        Calling this function has the side effect that the
        ``next_scheduled`` attribute will be updated to the new time
        in utc.
        """
        _update_schedule([self], time)

    def utc_of_next_schedule(self, current_time):
        """The time in UTC of this instance's next recurrence.

        :type current_time: :py:class:`datetime.datetime`
        :param current_time: The current time in utc.

        Usually this function does not need to be called directly, but
        will be used by ``update_schedule``. If however, you need to
        check when the next recurrence of a instance would happen,
        without persisting an update to the schedule, this funciton
        can be called without side-effect.
        """
        local_time = fleming.convert_to_tz(current_time, self.timezone)
        local_scheduled_time = fleming.fleming.dst_normalize(
            _replace_with_offset(local_time, self.offset, self.interval))
        utc_scheduled_time = fleming.convert_to_tz(local_scheduled_time, pytz.utc, return_naive=True)
        if utc_scheduled_time <= current_time:
            additional_time = {
                'DAY': timedelta(days=1),
                'WEEK': timedelta(weeks=1),
                'MONTH': relativedelta(months=1),
                'QUARTER': relativedelta(months=3),
                'YEAR': relativedelta(years=1),
            }
            utc_scheduled_time = fleming.add_timedelta(
                utc_scheduled_time, additional_time[self.interval], within_tz=self.timezone)

        return utc_scheduled_time


def _update_schedule(recurrences, time=None):
        """Update the schedule times for all the provided recurrences.
        """
        time = time or datetime.utcnow()
        for recurrence in recurrences:
            recurrence.next_scheduled = recurrence.utc_of_next_schedule(time)
            recurrence.previous_scheduled = time
            recurrence.save()


def _replace_with_offset(dt, offset, interval):
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
        _, last_day = calendar.monthrange(dt.year, dt.month)
        day = (offset.days + 1) if (offset.days + 1) <= last_day else last_day
        dt_out = dt.replace(day=day, hour=hours, minute=minutes, second=seconds)
    elif interval == 'quarter':
        month_range = [[1, 2, 3], [4, 5, 6], [7, 8, 9], [10, 11, 12]][int((dt.month - 1) / 3)]
        quarter_days = sum(calendar.monthrange(dt.year, month)[1] for month in month_range)
        days = offset.days if offset.days <= (quarter_days - 1) else (quarter_days - 1)
        dt_out = fleming.floor(dt, month=3).replace(hour=hours, minute=minutes, second=seconds)
        dt_out += timedelta(days)
    elif interval == 'year':
        leap_year_extra_days = 1 if calendar.isleap(dt.year) else 0
        days = offset.days if offset.days <= 364 + leap_year_extra_days else 364 + leap_year_extra_days
        dt_out = fleming.floor(dt, year=1).replace(hour=hours, minute=minutes, second=seconds)
        dt_out += timedelta(days)
    else:
        raise ValueError('{i} is not a proper interval value'.format(i=interval))
    return dt_out
