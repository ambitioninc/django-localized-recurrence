Installation
============

Installation with Pip
---------------------

Django Localized Recurrence is available on PyPi it can be installed using ``pip``::

    pip install django-localized-recurrence

Use with Django
---------------

To use Localized Recurrence with django, first be sure to install it
and/or include it in your ``requirements.txt`` Then include
``'localized_recurrence'`` in ``settings.INSTALLED_APPS``. After it is
included in your installed apps, run::

    ./manage.py migrate localized_recurrence

if you are using South_. Otherwise run::

    ./manage.py syncdb

.. _South: http://south.aeracode.org/
