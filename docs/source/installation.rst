Installation
==================================================

The Localized Recurrence is currently only available through
github. The intention is to make it available on Pypi, but until then
it can be installed through pip with::

    pip install git+git://github.com/ambitioninc/django-localized-recurrence.git@master

Use with Django
--------------------------------------------------

To use Localized Recurrence with django, first include it in your
``requirements.txt`` file as::

    git+git://github.com/ambitioninc/django-localized-recurrence.git@master

Then include `localized_recurrence` in `INSTALLED_APPS`. After it is
included in your installed apps, run::

    manage.py syncdb

