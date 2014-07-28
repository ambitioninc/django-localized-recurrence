Quickstart and Basic Usage
==========================

Django localized recurrence allows you to store a single instance of
the ``LocalizedRecurrence`` model for an event that occurs
regularly. Localized recurrences also automatically ensure that the
events remain consistent for the users local times.

The basic usage of the library comes in two steps:

1. Create a recurrence to keep track of a recurring event.
2. When appropriate, check if the event is due to be acted on, and
   take the appropriate action.

Creating a recurrence
---------------------

Creating a recurring event is as simple as creating an instance of
:py:class:`localized_recurrence.models.LocalizedRecurrence` using the
standard ``create`` method of django model managers. The following is
an example of a daily recurring event, at 3:00 PM in the user's local
time in the Eastern United States.

.. code-block:: python

    from datetime import timedelta

    from localized_recurrence.models import LocalizedRecurrence

    LocalizedRecurrence.objects.create(
        interval='DAY',
        offset=timedelta(hours=15),
        timezone='US/Eastern',
    )

Once a localized recurrence is created, it is simply a static object
in the database. However, it comes with methods that make it extremely
easy to know if the recurrence is due to be acted on.


Acting on a recurrence
----------------------

Django localized-recurrence does not specify a method for checking
when recurrences are due. The user of this app is in complete control
of how these recurrences are to be checked. For example, they could be
checked in the view code when a user loads a page, or in a celery beat
task.

In order to support a broad range of use cases, localized-recurrence
limits itself to two actions.

1. Checking when the event is next scheduled to recur.
2. Updating the event to have occured in this interval.

Acting on a single recurrence object
````````````````````````````````````

Given a ``LocalizedRecurrence`` object, called, say
``my_daily_event``, checking when an object is next scheduled to
recurr is as simple as checking the ``next_scheduled`` property of a
recurrence instance, which stores the time, in UTC, of when it is next
due.

.. code-block:: python

    if my_daily_event.next_scheduled < datetime.utcnow():
        # Process the event / Do stuff.

Then, once you are done processing the event, its schedule needs to be
updated so that it will not be due to be scheduled until its interval
has passed. This is as simple as calling the ``update_schedule``
method on the instance.

.. code-block:: python

    my_daily_event.update_schedule()

Calling this method updates the ``next_scheduled`` field on the model
in a way that makes sure it will recur only at the appropriate time
for its interval and timezone.


Acting on many recurrence objects
`````````````````````````````````

To find all the ``LocalizedRecurrence`` instance which are due we can
use django's built in ORM tools to filter based on the current UTC time.

.. code-block:: python

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
