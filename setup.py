import re
from setuptools import setup, find_packages

import multiprocessing
assert multiprocessing


def get_version():
    """
    Extracts the version number from the version.py file.
    """
    VERSION_FILE = 'localized_recurrence/version.py'
    mo = re.search(r'^__version__ = [\'"]([^\'"]*)[\'"]', open(VERSION_FILE, 'rt').read(), re.M)
    if mo:
        return mo.group(1)
    else:
        raise RuntimeError('Unable to find version string in {0}.'.format(VERSION_FILE))


setup(
    name='django-localized-recurrence',
    version=get_version(),
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    license='MIT License',
    description='Store events that recur in users\' local times.',
    long_description=open('README.rst').read(),
    author='Erik Swanson',
    author_email='theerikswanson@gmail.com',
    classifiers=[
        'Environment :: Web Environment',
        'Framework :: Django',
        'Framework :: Django :: 2.0',
        'Framework :: Django :: 2.1',
        'Framework :: Django :: 2.2',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
    ],
    install_requires=[
        'Django>=2.0',
        'ambition-django-timezone-field>=2.0.2',
        'fleming>=0.5.0',
        'python-dateutil',
        'pytz',
    ],
    tests_require=[
        'django-nose>=1.4',
        'django-dynamic-fixture',
        'mock',
    ],
    test_suite='run_tests.run_tests'
)
