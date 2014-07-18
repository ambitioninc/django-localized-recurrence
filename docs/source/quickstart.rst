Quickstart and Basic Usage
==================================================

Django localized recurrence allows you to store a single instance of
the LocalizedRecurrence model for an event that occurs
regularly. Localized recurrences also automatically ensure that the
events remain consistent for the users local times.

The basic usage of the library comes in two steps:

1. Create a recurrence to keep track of a recurring event
2. When appropriate, check if the event is due to be acted on, and
   take the appropriate action.

After describing the basic usage, this document will give a more
detailed description of a possible use case.

Creating a recurrence
--------------------------------------------------

The following is an example of a daily recurring event, at 3:00 PM in
the user's local time in the Eastern United States. ::

    from datetime import timedelta

    from localized_recurrence.models import LocalizedRecurrence

    LocalizedRecurrence.objects.create(
        interval='DAY',
        offset=timedelta(hours=15),
        timezone='US/Eastern',
    )

The arguments to create this event are:

- interval: One of the three character strings: 'DAY', 'WEEK', or
  'MONTH', specifying how often the event happens.

- offset: A python timedelta containing the amount of time into the
  interval the event is supposed to recur. That is, if the interval is
  daily, then a recurrence at 3:00 PM daily would correspond to an
  ``offset`` of ``timedelta(hours=15)``. If the interval is weekly, then a
  recurrence at 1:00 AM on Tuesday would correspond to an ``offset`` of
  ``timedelta(days=1, hours=1)``.

- timezone: A string (or timezone object) that can be accepted into a
  pytz timezone_field, representing the timezone of the user.

Acting on a recurrence
--------------------------------------------------

Django localized-recurrence does not specify a method for checking
when recurrences are due. The user of this app is in complete control
of how these recurrences are to be checked. For example, they could be
checked in the view code when a user loads a page, or in a celery beat
task.

In order to support a broad range of use cases, localized-recurrence
limits itself to two actions.

1. Checking when the event is next scheduled to recur.
2. Updating the event to have occured in this interval.

With this model, the first step is to check if a ``LocalizedRecurrence``
is due to occur. For a given ``LocalizedRecurrence`` object, called, say
``my_daily_event``, this check is as simple as::

    my_daily_event.next_scheduled < datetime.utcnow()

Or, to find all the ``LocalizedRecurrence`` instance which are due::

    past_due = LocalizedRecurrence.objects.filter(next_scheduled__lte=datetime.utcnow())

Then, after taking whatever action goes along with an event, we need
to update the database so that the types of checks we showed above
will only return ``True`` in the next interval for the recurrence.

For a queryset, such as ``past_due`` above, this is as simple as::

    past_due.update_schedule()

With that call, django-localized-recurrence takes care of any local
time changes in the interval, and sets the ``next_scheduled`` field of
each object to the time, in UTC, of the event, as the user would
expect it for their local time.

To update a single record, first filter to that get record::

     LocalizedRecurrence.objects.filter(id=my_daily_event.id).update_schedule()

