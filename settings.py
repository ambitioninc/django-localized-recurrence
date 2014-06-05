import os

from django.conf import settings

def configure_settings():
    """
    Configures settings for manage.py and for run_tests.py.
    """
    if not settings.configured:
        # Determine the database settings depending on if a test_db var is set in CI mode or not
        test_db = os.environ.get('DB', 'sqlite')
        if test_db == 'sqlite':
            db_config = {
                'ENGINE': 'django.db.backends.sqlite3'
            }
        elif test_db == 'postgres':
            db_config = {
                'ENGINE': 'django.db.backends.postgresql_psycopg2',
                'USER': 'postgres',
                'NAME': 'localized_recurrence',
            }
        else:
            raise RuntimeError('Unsupported test DB {0}'.format(test_db))

        settings.configure(
            DATABASES={
                'default': db_config,
            },
            INSTALLED_APPS=(
                'django.contrib.auth',
                'django.contrib.contenttypes',
                'django.contrib.sessions',
                'django.contrib.admin',
                'south',
                'localized_recurrence',
                'localized_recurrence.tests',
            ),
            ROOT_URLCONF='localized_recurrence.urls',
            DEBUG=False,
        )

