"""
Django settings for campusmgmt project.

For more information on this file, see
https://docs.djangoproject.com/en/1.6/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.6/ref/settings/
"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os
from os.path import join, abspath, dirname
BASE_DIR = os.path.dirname(os.path.dirname(__file__))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.6/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'r(sx+j3#e5@_tkx+y-c26h33fxa3^)e4s2rm989!0sa*p&43)q'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

TEMPLATE_DEBUG = DEBUG

ALLOWED_HOSTS = []
root = lambda *x: join(abspath(BASE_DIR), *x)

# Application definition

INSTALLED_APPS = (
    #'grappelli.dashboard',
    #'xadmin',

    #'bootstrap',
    'django_forms_bootstrap',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_para',
    'django_extensions',
    'crispy_forms',
    'main',
    'sitetree',
    'massadmin',
    'localflavor',
    'dajax',
    'dajaxice',

    'reversion',
    'grappelli',
    'profiles',
    'administration',
    'schedule',
    'discipline',
    'attendance',
    'grades',
    'ajax_select',
    #'djcelery'
    'djangocrudgenerator',
    'daterange_filter',
    'django_filters',
    'pagination',

    'admin_export',
    'custom_field',
    'ckeditor',
    'report_builder',
    'responsive_dashboard',
    #'simple_import',
    'djangobower',
    #'scaffold_report',
    'django_su',
    'floppy_gumby_forms',
    'floppyforms',
    'widget_tweaks',
    'django_cached_field',
    #'work_study',
    'engrade_sync',
    'django_extensions',
    #'south'
    )

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

ROOT_URLCONF = 'campusmgmt.urls'

WSGI_APPLICATION = 'campusmgmt.wsgi.application'



# Database
# https://docs.djangoproject.com/en/1.6/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2', # Add 'postgresql_psycopg2', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': 'campus',                      # Or path to database file if using sqlite3.
        'USER': 'vikas',                      # Not used with sqlite3.
        'PASSWORD': 'garg88',                  # Not used with sqlite3.
        'HOST': '',                      # Set to empty string for localhost. Not used with sqlite3.
        'PORT': '5432',                      # Set to empty string for default. Not used with sqlite3.
    }
}
'''

 'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2', # Add 'postgresql_psycopg2', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': 'campus',                      # Or path to database file if using sqlite3.
        'USER': 'vikas',                      # Not used with sqlite3.
        'PASSWORD': 'garg88',                  # Not used with sqlite3.
        'HOST': '',                      # Set to empty string for localhost. Not used with sqlite3.
        'PORT': '5432',                      # Set to empty string for default. Not used with sqlite3.
    }
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'campusdb.sqlite3'),
    }
'''

# Internationalization
# https://docs.djangoproject.com/en/1.6/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True

PREFERED_FORMAT = 'o'

# Additional locations of static files
STATICFILES_DIRS = (
    os.path.join(BASE_DIR, 'static_files'),
    ('gumby_css', root('components/css/')),
)

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.6/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = root('static/')
MEDIA_URL = '/media/'
MEDIA_ROOT = root('media/')
CKEDITOR_UPLOAD_PATH = root('media/uploads')


#BOWER
BOWER_COMPONENTS_ROOT = root('components/')

BOWER_INSTALLED_APPS = (
    'jquery',
    'jquery-ui',
    'gumby',
    'jquery-migrate',
    'blockui',
    'jquery-color',
)

#GRAPPELLI
#ADMIN_TOOLS_MENU = 'menu.CustomMenu'
ADMIN_MEDIA_PREFIX = STATIC_URL + "grappelli/"
#GRAPPELLI_INDEX_DASHBOARD = 'dashboard.CustomIndexDashboard'
GRAPPELLI_ADMIN_TITLE = '<img src="/static/images/logo.png"/ style="height: 30px; margin-left: -10px; margin-top: -8px; margin-bottom: -11px;">'


AUTHENTICATION_BACKENDS = ('django.contrib.auth.backends.ModelBackend',)

#LDAP
LDAP = False
if LDAP:
    LDAP_SERVER = 'admin.example.org'
    NT4_DOMAIN = 'ADMIN'
    LDAP_PORT = 389
    LDAP_URL = 'ldap://%s:%s' % (LDAP_SERVER, LDAP_PORT)
    SEARCH_DN = 'DC=admin,DC=example,DC=org'
    SEARCH_FIELDS = ['mail','givenName','sn','sAMAccountName','memberOf', 'cn']
    BIND_USER = 'ldap'
    BIND_PASSWORD = ''
    AUTHENTICATION_BACKENDS += ('ldap_groups.accounts.backends.ActiveDirectoryGroupMembershipSSLBackend',)

#Google Apps
GAPPS = False
if GAPPS:
    GAPPS_DOMAIN = ''
    GAPPS_USERNAME = ''
    GAPPS_PASSWORD = ''
    GAPPS_ALWAY_ADD_GROUPS = False
    AUTHENTICATION_BACKENDS += ('google_auth.backends.GoogleAppsBackend',)

#AUTHENTICATION_BACKENDS += ('django_su.backends.SuBackend',)


#Django AJAX selects
AJAX_LOOKUP_CHANNELS = {
    # the simplest case, pass a DICT with the model and field to search against :
    'student' : ('profiles.lookups', 'StudentLookup'),
    'all_student' : ('profiles.lookups', 'AllStudentLookup'),
    'dstudent' : ('profiles.lookups', 'StudentLookupSmall'),
    'faculty' : ('profiles.lookups', 'FacultyLookup'),
    'faculty_user' : ('profiles.lookups', 'FacultyUserLookup'),
    'attendance_quick_view_student': ('attendance.lookups', 'AttendanceAddStudentLookup'),
    'emergency_contact' : ('profiles.lookups', 'EmergencyContactLookup'),
    'attendance_view_student': ('attendance.lookups', 'AttendanceStudentLookup'),
    'discstudent' : ('discipline.lookups', 'StudentWithDisciplineLookup'),
    'discipline_view_student': ('discipline.lookups', 'DisciplineViewStudentLookup'),
    'volunteer': ('volunteer_track.lookups', 'VolunteerLookup'),
    'site': ('volunteer_track.lookups', 'SiteLookup'),
    'site_supervisor': ('volunteer_track.lookups', 'SiteSupervisorLookup'),
    'theme': ('omr.lookups', 'ThemeLookup'),
    'studentworker' : ('work_study.lookups', 'StudentLookup'),
    'company_contact':('work_study.lookups','ContactLookup'),
    'course': {'model':'schedule.course', 'search_field':'fullname'},
    'day': ('schedule.lookups','DayLookup'),
    'company'  : {'model':'work_study.workteam', 'search_field':'team_name'},
    'benchmark' : ('omr.lookups', 'BenchmarkLookup'),
}

#CKEDITOR
CKEDITOR_MEDIA_PREFIX = "/static/ckeditor/"
CKEDITOR_UPLOAD_PATH = MEDIA_ROOT + "uploads"
CKEDITOR_CONFIGS = {
    'default': {
        'toolbar': [
            [ 'Bold', 'Italic', 'Underline', 'Subscript','Superscript',
              '-', 'Image', 'Link', 'Unlink', 'SpecialChar', 'equation',
              '-', 'Format',
              '-', 'Maximize',
              '-', 'Table',
              '-', 'BulletedList', 'NumberedList',
              '-', 'PasteText','PasteFromWord',
            ]
        ],
        'height': 120,
        'width': 640,
        'disableNativeSpellChecker': False,
        'removePlugins': 'scayt,menubutton,contextmenu,liststyle,tabletools,tableresize,elementspath',
        'resize_enabled': False,
        'extraPlugins': 'equation',
    },
}



STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'djangobower.finders.BowerFinder',
)

CRISPY_TEMPLATE_PACK='bootstrap'

TEMPLATE_DIRS = (
    root('templates/'),
)

TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
    'apptemplates.Loader',
    'django.template.loaders.eggs.Loader',
)

#Engrade
# http://ww7.engrade.com/api/key.php
ENGRADE_APIKEY = ''
ENGRADE_LOGIN = ''
ENGRADE_PASSWORD = ''
# School UID (admin must be connected to school)
ENGRADE_SCHOOLID = ''


# Global date validators, to help prevent data entry errors
import datetime
from django.core.validators import MinValueValidator # Could use MaxValueValidator too
DATE_VALIDATORS=[MinValueValidator(datetime.date(1970,1,1))] # Unix epoch!

TEMPLATE_CONTEXT_PROCESSORS = (
                "django.contrib.auth.context_processors.auth",
                "django.core.context_processors.debug",
                "django.core.context_processors.i18n",
                "django.core.context_processors.media",
                "django.core.context_processors.static",
                "django.contrib.messages.context_processors.messages",
                "django.core.context_processors.request"
                )
# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error when DEBUG=False.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        }
    },
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler'
        }
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
    }
}
# Parse database configuration from $DATABASE_URL

import dj_database_url
DATABASES['default'] =  dj_database_url.config()

# Honor the 'X-Forwarded-Proto' header for request.is_secure()
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Allow all host headers
ALLOWED_HOSTS = ['*']

# Static asset configuration
import os
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_ROOT = 'staticfiles'
STATIC_URL = '/static/'

STATICFILES_DIRS = (
    os.path.join(BASE_DIR, 'static'),
)
