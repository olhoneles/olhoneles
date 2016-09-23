# Django settings for olhoneles project.

import os
import sys
from derpconf.config import Config

INSTANCE = lambda *x: os.path.join(os.path.dirname(__file__), *x)

if 'test' in sys.argv:
    config_file = INSTANCE('tests.config')
else:
    config_file = INSTANCE('local.config')

if os.path.isfile(config_file):
    conf = Config.load(config_file)
else:
    conf = Config()

DEBUG = conf.get('DEBUG', True)

ADMINS = conf.get('ADMINS', ())

MANAGERS = ADMINS

DEAFAULT_DATABASE = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': INSTANCE('db.sqlite3'),
        'USER': '',
        'PASSWORD': '',
        'HOST': '',
        'PORT': '',
    }
}

DATABASES = conf.get('DATABASES', DEAFAULT_DATABASE)

# Hosts/domain names that are valid for this site; required if DEBUG is False
# See https://docs.djangoproject.com/en/1.5/ref/settings/#allowed-hosts
ALLOWED_HOSTS = conf.get('ALLOWED_HOSTS', [])

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# In a Windows environment this must be set to your system time zone.
TIME_ZONE = conf.get('TIME_ZONE', 'America/Chicago')

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = conf.get('LANGUAGE_CODE', 'en-us')

SITE_ID = conf.get('SITE_ID', 1)

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = conf.get('USE_I18N', True)

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale.
USE_L10N = conf.get('USE_L10N', True)

# If you set this to False, Django will not use timezone-aware datetimes.
USE_TZ = conf.get('USE_TZ', True)

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/var/www/example.com/media/"
MEDIA_ROOT = conf.get('MEDIA_ROOT', INSTANCE('../media'))

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://example.com/media/", "http://media.example.com/"
MEDIA_URL = conf.get('MEDIA_URL', '/media/')

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/var/www/example.com/static/"
STATIC_ROOT = conf.get('STATIC_ROOT', '')

# URL prefix for static files.
# Example: "http://example.com/static/", "http://static.example.com/"
STATIC_URL = conf.get('STATIC_URL', '/static/')

# Additional locations of static files
STATICFILES_DIRS = (
    # Put strings here, like "/home/html/static" or "C:/www/django/static".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
)

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
#    'django.contrib.staticfiles.finders.DefaultStorageFinder',
)

# Make this unique, and don't share it with anybody.
SECRET_KEY = conf.get('SECRET_KEY', 'REPLACE-THIS-IN-CONFIG-LOCAL')

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.contrib.auth.context_processors.auth',
                'django.template.context_processors.debug',
                'django.template.context_processors.i18n',
                'django.template.context_processors.media',
                'django.template.context_processors.static',
                'django.template.context_processors.tz',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    # Uncomment the next line for simple clickjacking protection:
    # 'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

ROOT_URLCONF = 'olhoneles.urls'

# Python dotted path to the WSGI application used by Django's runserver.
WSGI_APPLICATION = 'olhoneles.wsgi.application'

DEFAULT_INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.admin',
    'bootstrap_toolkit',
    'easy_thumbnails',
    'montanha',
    'cms',
    'captcha',
    'raven.contrib.django.raven_compat',
)

INSTALLED_APPS = conf.get('INSTALLED_APPS', DEFAULT_INSTALLED_APPS)

# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error when DEBUG=False.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'root': {
        'level': 'WARNING',
        'handlers': ['sentry'],
    },
    'formatters': {
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s'
        },
    },
    'handlers': {
        'sentry': {
            'level': 'ERROR',
            'class': 'raven.contrib.django.raven_compat.handlers.SentryHandler',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose'
        }
    },
    'loggers': {
        'django.db.backends': {
            'level': 'ERROR',
            'handlers': ['console'],
            'propagate': False,
        },
        'raven': {
            'level': 'DEBUG',
            'handlers': ['console'],
            'propagate': False,
        },
        'sentry.errors': {
            'level': 'DEBUG',
            'handlers': ['console'],
            'propagate': False,
        },
    },
}

THUMBNAIL_ALIASES = {
    '': {
        'mini': {'size': (20, 20), 'crop': False},
    },
}

DEFAULT_CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache',
        'LOCATION': INSTANCE('../cache'),
    }
}

CACHES = conf.get('CACHES', DEFAULT_CACHES)

DEFAULT_FROM_EMAIL = conf.get('DEFAULT_FROM_EMAIL', 'montanha-dev@listas.olhoneles.org')

CONTACT_US_EMAIL = conf.get('CONTACT_US_EMAIL', 'montanha@olhoneles.org')

SERVER_EMAIL = conf.get('SERVER_EMAIL', 'montanha@olhoneles.org')

RECAPTCHA_PUBLIC_KEY = conf.get('RECAPTCHA_PUBLIC_KEY', '')
RECAPTCHA_PRIVATE_KEY = conf.get('RECAPTCHA_PRIVATE_KEY', '')

RAVEN_CONFIG = conf.get('RAVEN_CONFIG', {'dsn': ''})
