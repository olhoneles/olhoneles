#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages
from olhoneles import __version__

tests_require = [
    'nose',
    'coverage',
    'factory_boy',
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
        'Django>=1.6.1,<1.7.0',
        'Pillow>=2.3.1,<2.4.0',
        'South>=0.8.4,<0.9.0',
        'django-parsley>=0.4,<0.5.0',
        'django-bootstrap-toolkit==2.14',
        'easy-thumbnails>=2.2.0,<2.3.0',
        'requests>=2.2.1,<2.3.0',
        'chardet>=2.2.1,<2.3.0',
        'pandas>=0.13.1,<0.14.0',
        'derpconf>=0.4.9,<0.5.0',
        'django-recaptcha>=0.0.9,<0.1.0',
        'raven>=5.26.0,<=5.27.0',
    ],
    dependency_links = [
        'https://github.com/gnoronha/django-bootstrap-toolkit/archive/0f0ff43eeab8e19ee8d8021460f1a4abf8303bde.zip#egg=django-bootstrap-toolkit-2.14'
    ],
    extras_require={
        'tests': tests_require,
    },
)
