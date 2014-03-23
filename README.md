Django Localized Recurrence
===========================

Store events that recur in users' local times.

Overview
----------------------------------------

Your site has a lot of uses, spread across different timezones. You
want the allow them to schedule recurring events.

Without localized recurrences, it is difficult to ensure that
something happens at 3:00 PM every Wednesday in a User's local
time. With localized recurrences, it is easy.

Installation
----------------------------------------

This packages is currently only available through github. The
intention is to make it available on Pypi, but until then it can be
installed through pip with:

    pip install git+git://github.com/ambitioninc/django-localized-recurrence.git@master


Usage
----------------------------------------

### Creating a recurrence

The following is an example of a daily recurring event, at 3:00 PM in
the user's local time in the Eastern United States.

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

- offset: A python The amount of time into the interval 

- timezone: A string (or timezone object) that can be accepted into a
  pytz timezone_field, representing the timezone of the user.

### Acting on a recurrence

Django localized-recurrence does not specify a method for checking
when recurrences are due. The user of this app is in complete control
of how these recurrences are to be checked. For example, they could be
checked in the view code when a user loads a page, or in a celery beat
task.


Contributions and Licence
----------------------------------------

Licenced under the BSD Licence. For details see the LICENCE file.
