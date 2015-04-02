.. image:: https://travis-ci.org/Wilduck/django-localized-recurrence.svg?branch=develop
    :target: https://travis-ci.org/Wilduck/django-localized-recurrence

Django Localized Recurrence
===========================
Django Localized Recurrence allowes you to store events that recur in
users' local times, and not have to worry about things like

This django app provides a model, ``LocalizedRecurrence``, with
methods to help store recurring events, check if the events are due,
and update their next scheduled time.

Installation
------------
This packages is currently available through Pypi and github. To
install from Pypi using ``pip`` (recommended):

.. code-block:: none

    pip install django-localized-recurrence

To install the development version from github:

.. code-block:: none

    pip install git+git://github.com/ambitioninc/django-localized-recurrence.git@develop

Documentation
-------------
Full documentation is available at http://django-localized-recurrence.readthedocs.org

License
-------
MIT License (see LICENSE)
