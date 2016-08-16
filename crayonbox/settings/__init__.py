"""
Django settings for crayonbox project.

Generated by 'django-admin startproject' using Django 1.8.3.

For more information on this file, see
https://docs.djangoproject.com/en/1.8/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.8/ref/settings/
"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os
import djcelery
from celery.schedules import crontab

djcelery.setup_loader()

BASE_DIR = os.path.abspath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'very-secret-password'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

TEST_RUNNER = 'crayonbox.settings.test_runner.NoLoggingTestRunner'

ALLOWED_HOSTS = []
APPEND_SLASH = False

LOGIN_REDIRECT_URL = "/"
LOGIN_URL = "/login"
LOGOUT_URL = "/logout"

# Ignore the presence of gerrit variable as builds are trigerred from
# gerrit by default which means they are actually a 'baseline'
# Default is False meaning that presence of gerrit variables equals to
# 'patched' build. When the variable is set to True, gerrit is also not
# commented with test results.
IGNORE_GERRIT = False

AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
)

HOST = "art-reports.linaro.org"

# Application definition
INSTALLED_APPS = (
    'longusername',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.postgres',

    # 3rd party apps
    'rest_framework',
    'rest_framework.authtoken',
    'djcelery',
    'kombu.transport.django',

    # local apps
    'benchmarks',
    'api',
    'userprofile',
    'frontend'
)

DATETIME_FORMAT = "%d-%m-%Y %H:%M:%S"

REST_FRAMEWORK = {
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
    ),
    'DEFAULT_FILTER_BACKENDS': (
        'rest_framework.filters.DjangoFilterBackend',
        'rest_framework.filters.OrderingFilter',),
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.BasicAuthentication',
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.TokenAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_PAGINATION_CLASS': 'api.pagination.Pagination',
    'PAGE_SIZE': 20
}

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    #'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.security.SecurityMiddleware',
)

ROOT_URLCONF = 'crayonbox.urls'

TEMPLATES = [{
    'BACKEND': 'django.template.backends.django.DjangoTemplates',
    'DIRS': [BASE_DIR + '/templates'],
    'APP_DIRS': True,
    'OPTIONS': {
        'context_processors': [
            'django.template.context_processors.debug',
            'django.template.context_processors.request',
            'django.contrib.auth.context_processors.auth',
            'django.contrib.messages.context_processors.messages',
        ],
    }
}]

WSGI_APPLICATION = 'crayonbox.wsgi.application'

BENCHMARK_MANIFEST_PROJECT_LIST = [
    'linaro-art/platform/bionic',
    'linaro-art/platform/build',
    'linaro-art/platform/external/vixl',
    'linaro-art/platform/art'
]

CREDENTIALS = {
    'host.url.netloc': ('username', 'password'),
}

UPDATE_JENKINS = False

# Internationalization
# https://docs.djangoproject.com/en/1.8/topics/i18n/
LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True
USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.8/howto/static-files/
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static')

# Celery settings
BROKER_URL = 'amqp://guest:guest@localhost:5672//'

CELERY_RESULT_BACKEND = 'rpc://'
CELERY_RESULT_PERSISTENT = False
CELERY_ACCEPT_CONTENT = ['json', 'pickle']
CELERYBEAT_SCHEDULE_FILENAME = "/tmp/celery-beat"

CELERYD_LOG_FORMAT = '[%(asctime)s] %(levelname)s: %(message)s'
CELERYD_TASK_LOG_FORMAT = '[%(asctime)s] %(levelname)s %(task_name)s: %(message)s'
CELERY_TIMEZONE = 'UTC'

CELERYBEAT_SCHEDULE = {
    'Update External Repositories': {
        'task': 'benchmarks.tasks.sync_external_repos',
        'schedule': crontab(minute=0, hour='*/12'),
    },
    'Check for incopleted TestJobs': {
        'task': 'benchmarks.tasks.check_testjob_completeness',
        'schedule': crontab(minute='*/10'),
    },
    'Check for copleted Build': {
        'task': 'benchmarks.tasks.check_result_completeness',
        'schedule': crontab(minute='*/10'),
    },
    'Weekly Benchmark Progress': {
        'task': 'benchmarks.tasks.weekly_benchmark_progress',
        'schedule': crontab(minute=0, hour=9, day_of_week='1'),
    },
    'Monthly Benchmark Progress': {
        'task': 'benchmarks.tasks.monthly_benchmark_progress',
        'schedule': crontab(minute=0, hour=9, day_of_month='1'),
    }
}

LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'simple': {
            'format': u'[%(asctime)s] %(levelname)-8s %(message)s',
        }
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'celery': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'tasks': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': True,
        }
    }
}

EXTERNAL_DIR = {
    "BASE": os.path.join(BASE_DIR, 'ext'),
    "REPOSITORIES": [("art-testing", "https://android-review.linaro.org/linaro/art-testing")]
}
