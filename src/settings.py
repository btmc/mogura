# Django settings for mogura project.

import os, sys
import mysql.connector
from resource_loader import load

resources = load('/data/conf/resources.ini')

location = lambda x: os.path.join(
    os.path.dirname(os.path.realpath(__file__)), x)

BASE_DIR = '/data/mogura'

DEBUG = True 

ADMINS = (
    # ('Your Name', 'your_email@example.com'),
	('testadmin', 'testadmin@me.com')
)

MANAGERS = ADMINS

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# In a Windows environment this must be set to your system time zone.
TIME_ZONE = 'Europe/Moscow'

DATABASES = {
    'default': {
#        'ENGINE': 'django.db.backends.mysql', # Add 'postgresql_psycopg2', 'mysql', 'sqlite3' or 'oracle'.
#        'ENGINE': 'mysql.connector.django', # Add 'postgresql_psycopg2', 'mysql', 'sqlite3' or 'oracle'.
        'ENGINE': 'mysql_connector_python_django_mod', # Add 'postgresql_psycopg2', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': resources.get('mogura', 'mysql_db'),                      # Or path to database file if using sqlite3.
        'USER': resources.get('mogura', 'mysql_user'),                      # Not used with sqlite3.
        'PASSWORD': resources.get('mogura', 'mysql_password'),                  # Not used with sqlite3.
        'HOST': resources.get('mogura', 'mysql_host'),                      # Set to empty string for localhost. Not used with sqlite3.
        'PORT': '',                      # Set to empty string for default. Not used with sqlite3.
        'OPTIONS':  {
                        'time_zone': TIME_ZONE, 'ssl_disabled': True,
                    }
    }
}

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale.
USE_L10N = False

# If you set this to False, Django will not use timezone-aware datetimes.
#USE_TZ = True

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/home/media/media.lawrence.com/media/"
MEDIA_ROOT = ''

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://media.lawrence.com/media/", "http://example.com/media/"
MEDIA_URL = ''

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/home/media/media.lawrence.com/static/"
STATIC_ROOT = location('./static')

# URL prefix for static files.
# Example: "http://media.lawrence.com/static/"
STATIC_URL = '/static/'

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
SECRET_KEY = ''

ROOT_URLCONF = 'urls'

# Python dotted path to the WSGI application used by Django's runserver.
WSGI_APPLICATION = 'wsgi.application'

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'reports',
    'scheduler',
    'logger',
    # Uncomment the next line to enable the admin:
    'django.contrib.admin',
    # Uncomment the next line to enable admin documentation:
    'django.contrib.admindocs',
    'mptt',
    'feincms',
    'reversion',
    'reversion_compare',
)

LOGIN_URL = '/accounts/login'
LOGIN_REDIRECT_URL = '/'

STORE_DIR = '/mnt/mogura/cache'
UPLOAD_DIR = '/mnt/mogura/upload'

BEANSTALK_HOST = resources.get('mogura', 'beanstalk_host')
BEANSTALK_PORT = 11300
BEANSTALK_TTR = 86400 * 7

PGSQL_DSN = 'user=' + resources.get('mogura', 'pgsql_mogd_user') + ' password=' + resources.get('mogura', 'pgsql_mogd_password') + ' host=' + resources.get('mogura', 'pgsql_mogd_host') + ' port=5432'

DATE_FORMAT = 'Y-m-d'
DATETIME_FORMAT = 'Y-m-d H:i:s'

REPORT_CHUNK_SIZE = 100

ALLOWED_HOSTS = ['*']

TEMPLATES = [
    {
        'BACKEND'   :   'django.template.backends.django.DjangoTemplates',
        'DIRS'      :
            [
                'reports',
            ],
        'APP_DIRS'  :   True,
        'OPTIONS'   :
            {
                'context_processors'    :
                    [
                        'django.contrib.auth.context_processors.auth',
                        'django.template.context_processors.debug',
                        'django.template.context_processors.i18n',
                        'django.template.context_processors.media',
                        'django.template.context_processors.static',
                        'django.template.context_processors.tz',
                        'django.contrib.messages.context_processors.messages'
                    ],
                'debug'                 :   DEBUG,
            },
    } 
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

from settings_local import *