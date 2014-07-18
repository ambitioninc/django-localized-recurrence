Examples
========

A Calendar Event Example
------------------------

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
recurrences depends on the user actually visiting a page to hit the
code path. It would also be possible to check if the recurrences are
past due in a separate task, like the celery-beat scheduler.
