.. image:: https://travis-ci.org/Wilduck/django-localized-recurrence.svg?branch=develop
    :target: https://travis-ci.org/Wilduck/django-localized-recurrence

Django Localized Recurrence
===========================

Store events that recur in users' local times.

Overview
----------------------------------------

Your site has a lot of users, spread across different timezones. You
want the allow them to schedule recurring events. Without localized
recurrences, it is difficult to ensure that something happens at 3:00
PM every Wednesday in a User's local time. With localized recurrences,
it is easy.

The goal of this library is to automatically keep track of when your
users expect events to happen next, even across daylight savings time
boundaries, allowing you to interact with these events purely in UTC.

The Usage section of this document describes patterns for using
localized-recurrences in more detail.


Installation
----------------------------------------

This packages is currently available through Pypi and github. To
install from Pypi using ``pip`` (recommended):

.. code-block:: none

    pip install django-localized-recurrence

To install the development version from github:

.. code-block:: none

    git clone git+git://github.com/ambitioninc/django-localized-recurrence.git@develop
    cd django-localized-recurrence
    python setup.py install


Basic Usage: Scheduling
----------------------------------------


Creating a recurrence
````````````````````````````````````````

The following is an example of a daily recurring event, at 3:00 PM in
the user's local time in the Eastern United States.

.. code-block:: python

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
````````````````````````````````````````

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
``my_daily_event``, this check is as simple as:

.. code-block:: python

    my_daily_event.next_scheduled < datetime.utcnow()

Or, to find all the ``LocalizedRecurrence`` instance which are due:

.. code-block:: python

    past_due = LocalizedRecurrence.objects.filter(next_scheduled__lte=datetime.utcnow())

Then, after taking whatever action goes along with an event, we need
to update the database so that the types of checks we showed above
will only return ``True`` in the next interval for the recurrence.

For a queryset, such as ``past_due`` above, this is as simple as:

.. code-block:: python

    past_due.update_schedule()

With that call, django-localized-recurrence takes care of any local
time changes in the interval, and sets the ``next_scheduled`` field of
each object to the time, in UTC, of the event, as the user would
expect it for their local time.

To update a single record, first filter to that get record:

.. code-block:: python

     LocalizedRecurrence.objects.filter(id=my_daily_event.id).update_schedule()


A Calendar Event Example
````````````````````````````````````````

In this example we create a basic Calendar event, which store
recurring events. The benefits of using a localized recurrence in this
way are two fold. First, that you don't have to store a separate entry
for every time the event happens, only one localized recurrence
describing how the event recurs. Second, the code for keeping track of
the conversion between a user's local time and UTC, even across
daylight savings time boundaries is automatically handled by the
recurrence updates.

We start by defining a model with a foreign key to ``LocalizedRecurrence``.

.. code-block:: python

    from django.contrib.auth.models import User
    from django.db import models

    from localized_recurrence import LocalizedRecurrence

    class RecurringCalendarEvent(models.Model):
        user = models.ForeignKey(User)
        event_name = models.CharField(max_length=120)
        event_description = models.TextField()
        recurrence = models.ForeignKey(LocalizedRecurrence)

        objects = RecurringCalendarEventManager()

To go along with the event model, we create a manager that can create
the localized recurrence and event at the same time.

.. code-block:: python

    class RecurringCalendarEventManager(models.Manager):
        def create_event(self, name, description, user, timezone, offset, interval):
            recurrence = LocalizedRecurrence.objects.create(
                interval=interval,
                offset=time,
                timezone=timezone
            )
            event = self.create(
                user=user,
                event_name=name,
                description=description,
                recurrence=recurrence
            )
            return event

Then, in a file ``views.py`` we can create two views. The first is a
view that is intended to show a simple calendar but that first checks
to see if there are any events that are due to be shown the user. It
does this by filtering on the ``next_scheduled`` field of the associated
``LocalizedRecurrence`` objects.

.. code-block:: python

    from datetime import datetime

    from django.shortcuts import redirect
    from django.views.generic import TemplateView

    class CalendarView(TemplateView):
        template_name = 'calendar/full_calendar.html'

        def get(self, request, *args, **kwargs):
            events_past_due = RecurringCalendarEvent.objects.filter(
                user=self.request.user,
                recurrence__next_scheduled__lte=datetime.utcnow()
            )
            if events_past_due.count() > 0:
                redirect('calendar.event_notification')
            else:
                return super(CalendarView, self).get(request, *args, **kwargs)

The second view (also assumed to be in the ``views.py`` file) is the
view that displays any of the events that are past due. In this view,
the ``get_context_data`` takes care of both passing the events to the
template, but also updating the ``LocalizedRecurrence`` objects so that
their ``next_scheduled`` fields are automatically set to the appropriate
time in the future.

.. code-block:: python

    class CalendarNotification(TemplateView):
        template_name = 'calendar/event_notification.html'

        def get_context_data(self):
            context = super(CalendarNotification, self)
            events_past_due = RecurringCalendarEvent.objects.filter(
                user=self.request.user,
                recurrence__next_scheduled__lte=datetime.utcnow()
            )
            LocalizedRecurrence.objects.filter(
                id__in=[event.recurrence for event in events_past_due]
            ).update_schedule()
            context['events_past_due'] = events_past_due
            return context

Then all that's left is presenting this information in an attractive
manner.

In this usage of the LocalizedRecurrence objects, checking the
recurrences depend on the user actually visiting a page to hit the
code path. It would also be possible to check if the recurrences are
past due in a separate task, like the celery-beat scheduler.


Advanced Usage: Event Tracking
----------------------------------------

The dual to the scheduling problem, and another possible use for
localized recurrence, is keeping track of whether or not events have
actually occured in a given time period, as opposed to keeping track
of when an event is scheduled to occur. For example, a notifications
app could use localized recurrences to keep track of notifications
that should only be sent once every day.

Any localized recurrence to be used for this purpose should be
initiated with an ``offset`` of ``timedelta(0)``. For example:

.. code-block:: python

    from localized_recurrence.models import LocalizedRecurrence

    event_tracker = LocalizedRecurrence.objects.create(
        interval='DAY',
        offset=timedelta(0),
        timezone='US/Eastern'
    )

We'll show below how a recurrence of the form above could be used to
track the state of an event throughout a given time period.

Step Tracker Example
````````````````````````````````````````

Imagine running a website that recieves updates from users pedometers
about the number of steps they've taken. Modeling this requires a
model that keeps track of steps taken each day. Assume the pedometer
sends a request with the user's local date, and the number of steps
since the last check in. The code to keep track of that information
would look something like:

.. code-block:: python

    class StepsManager(models.Manager):
        def add_steps(self, user, date, steps):
            steps_obj, created = self.get_or_create(user=user, date=date)
            steps_obj.steps = steps_obj.steps + steps
            steps_obj.save()

    class Steps(models.Model):
        user = models.ForeignKey('User')
        date = models.DateField()
        total_steps = models.IntegerField(default=0)

        objects = StepsManager()

Users can also subscribe to get an email-notification whenever they
hit over a given number of steps in a single day. This is where a
localized recurrence can be used to help ensure that users are sent no
more than one email notification in a given day.

We can keep track of what notifications a user wishes to recieve in a
``StepsNotification`` model:

.. code-block:: python

    class StepsNotification(models.Model):
        user = models.ForeignKey('User', unique=True)
        steps_to_notify = models.IntegerField(default=10000)
        recurrence = models.ForeignKey('LocalizedRecurrence')

Then, a periodic task can be set up to check if the user has reached
their goal. This will also check that the associated recurrence is
past due by checking that it's ``next_scheduled`` value has already
passed (that is, it is less than ``utcnow()``).

.. code-block:: python

    def check_steps_and_notify(user):
        utc_now = datetime.utcnow()
        date = flemming.convert_to_tz(now, user.timezone)
        steps = Steps.objects.filter(date=date)
        notify = StepsNotification.objects.get(user=user)
        if steps > notify.steps and notify.recurrence.next_scheduled < now:
            msg = 'You reached your goal of {goal} steps today!'
            send_email(
                'You made your step goal',
                msg.format(goal=notify.steps)
                recipient_list=[user.email]
            )
            notify.recurrence.update_schedule()

Note that the recurrence is only updated if the step notification
condition is me.t This means that the recurrence ``next_scheduled``
value will always be less than ``utcnow()``, except in the case where
an email has already been sent that day.

Also, because the recurrences being used in this example have all been
initialized with ``offset=timedelta(0)``, when the call to
``update_schedule`` does occur, it updates to the start of the next
day in the user's local time, making sure that no duplicate emails are
sent in one day, but also making sure that a new email can be sent
for each day's goal.

This is how localized recurrences can be used to keep track of the
state of a notification, rather than keep track of the state of a
schedule.



Tracking Multiple Things with one Recurrence
````````````````````````````````````````````

Localized recurrences also come with the ability to track the state of
multiple objects, with the same base localized recurrence. This
feature is intended to make it simpler to track members of a mutable
group (with members occasionally added and removed), that are in the
same locale.

Given a recurrence, additional objects can be tracked/updated with:

.. code-block:: python

    my_recurrence.update_schedule(for_object=my_thing_to_track)

and their state can be checked with

.. code-block:: python

    my_recurrence.sub_recurrence(my_thing_to_track).next_scheduled

A call to ``update_schedule`` with a ``for_object`` argument, or a
call to ``sub_recurrence`` will try to find a the sub_recurrence
tracking the provided object, and create it if it does not already
exist. This allows a variable number of objects to be tracked, while
the consumer of the localized recurrence library only needs to track
one reference to a localized recurrence.

Finally, given a list of objects, it is possible to check all at once,
how many of them are due by using:

.. code-block:: python

    objs_due = my_recurrence.check_due(potentially_eventful)

The command above will filter out any objects from
``potentially_eventful`` that have already been acted upon in this
period, leaving only those objects who's ``next_scheduled`` value is
less than the current time. This method also works to minimized the
number of database queries needed to accomplish this task.

Contributions and Licence
----------------------------------------

Contributions are welcome, through issues or pull requests. If this
documentation is unclear, feel free to ask for clarification.

Licenced under the MIT License. For details see the LICENSE file.
