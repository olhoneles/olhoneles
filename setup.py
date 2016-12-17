#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages
from olhoneles import __version__

tests_require = [
    'nose',
    'nose-focus',
    'coverage',
    'factory_boy',
    'pycodestyle',
    'mock',
]

setup(
    name='olhoneles',
    version=__version__,
    description='Activities of the Brazilian legislators',
    long_description='''
A simple software to allow easier watching of the activities of the Brazilian
legislators
''',
    keywords='brazilian legislators web',
    author='OlhoNeles.org',
    author_email='montanha@olhoneles.org',
    url='http://olhoneles.org',
    license='AGPL',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU Affero General Public License v3 or later (AGPLv3+)',
        'Natural Language :: English',
        'Operating System :: POSIX :: Linux',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2.7',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
    ],
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'BeautifulSoup>=3.2.1,<3.3.0',
        'Django>=1.10.1,<1.11.0',
        'Pillow>=3.4.2,<3.5.0',
        'django-parsley>=0.4,<0.5.0',
        'django-bootstrap-toolkit==2.14',
        'easy-thumbnails>=2.3,<2.4',
        'requests>=2.6.0,<2.7.0',
        'chardet>=2.2.1,<2.3.0',
        'pandas>=0.13.1,<0.14.0',
        'derpconf>=0.8.0,<0.9.0',
        'django-recaptcha>=1.0.5,<1.1.0',
        'raven>=5.31.0,<=5.32.0',
        'django-localflavor>=1.3,<1.4.0',
        'django-cacheops>=3.1.1,<3.2.0',
        'python-dateutil>=2.6.0,<2.7.0',
        'django-tastypie>=0.13.3,<0.14.0',
        'django-tastypie-swagger==0.1.4-django1.10',
        'django-nose>=1.4.4,<1.5.0',
    ],
    dependency_links=[
        'https://github.com/gnoronha/django-bootstrap-toolkit/archive/0f0ff43eeab8e19ee8d8021460f1a4abf8303bde.zip#egg=django-bootstrap-toolkit-2.14',
        'https://github.com/olhoneles/django-tastypie-swagger/archive/fix-compatibility-django-1.10.zip#egg=django-tastypie-swagger-0.1.4-django1.10',
    ],
    extras_require={
        'tests': tests_require,
    },
)
