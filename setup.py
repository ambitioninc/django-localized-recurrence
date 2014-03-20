import os
from setuptools import setup, find_packages

README = open(os.path.join(os.path.dirname(__file__), 'README.md')).read()

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
    name='django-localized-recurrence',
    version='0.1dev',
    packages=find_packages(),
    include_package_data=True,
    license='BSD License', 
    description="Store events that recur in users' local times.",
    long_description=README,
    url='http://www.example.com/',
    author='Erik Swanson',
    author_email='theerikswanson@gmail.com',
    classifiers=[
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
    ],
    install_requires=[
        'django',
        'django-timezone-field',
        'fleming',
        'python-dateutil',
        'pytz',
    ],
    tests_require=[
        'django-nose',
        'south'
    ],
    test_suite='run_tests.run_tests'
)
