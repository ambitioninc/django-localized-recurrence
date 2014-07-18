Installation
============

Installation with Pip
---------------------

Django Localized Recurrence is available on PyPi it can be installed using ``pip``::

    pip install django-localized-recurrence

Use with Django
---------------

To use Localized Recurrence with django, first include it in your
``requirements.txt`` file as::

    django-localized-recurrence

Then include ``localized_recurrence`` in ``INSTALLED_APPS``. After it is
included in your installed apps, run::

    ./manage.py migrate localized_recurrence

if you are using South_. Otherwise run::

    ./manage.py syncdb

.. _South: http://south.aeracode.org/
