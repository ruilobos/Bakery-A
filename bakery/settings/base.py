"""
Base settings for the bakery project — this module *is* production (ADR-028).

Three modules, no `production.py`: this one, plus `local.py` and `test.py`, which
import from here and opt *into* convenient or unsafe behaviour. The accident
therefore lands on the safe side.

Every environment-sensitive value is read from the environment. The `default=`
fallbacks below reproduce the previous hardcoded values so that behaviour is
unchanged by the split:

  * task 2.1  removes the fallbacks for the secrets,
  * task 2.19 removes them entirely, at which point a missing variable raises
    `ImproperlyConfigured` at boot — `django-environ` already does this for a
    variable declared with no default, so no validator is needed.

2.19 is `Blocked` on roadmap question 9.22 (a raising module breaks
`collectstatic` at image build), which is why the fallbacks are still here.

See https://docs.djangoproject.com/en/3.2/ref/settings/
"""
import os

import environ

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

env = environ.Env()

# Read a local .env if one is present. Never committed — see .gitignore.
environ.Env.read_env(os.path.join(os.path.dirname(BASE_DIR), '.env'))

# SECURITY WARNING: keep the secret key used in production secret!
# The fallback is the prototype's committed key and is removed by task 2.1.
SECRET_KEY = env(
    'SECRET_KEY',
    default='django-insecure-ix12cqf%&1zw#a+cx_&%2wx)1n%7u^ocwp4j3=)9%qr8bu42s%',
)

# SECURITY WARNING: don't run with debug turned on in production!
# Defaults to False here because this module is production; `local.py` turns it on.
DEBUG = env.bool('DEBUG', default=False)

ALLOWED_HOSTS = env.list(
    'ALLOWED_HOSTS',
    default=['localhost', '127.0.0.1', '192.168.0.191', 'bakery.loboserver.com'],
)


# Application definition

INSTALLED_APPS = [
    'core.apps.CoreConfig',
    'accounts.apps.AccountsConfig',
    'control.apps.ControlConfig',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'mathfilters',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'bakery.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'bakery.wsgi.application'


# Database - PostgreSQL
# https://docs.djangoproject.com/en/3.2/ref/settings/#databases
#
# DATABASE_URL is the database contract (ADR-015 rule 2), so the same image runs
# on any host that can supply one. The fallback reproduces the previous hardcoded
# credentials and is removed by task 2.1.

DATABASES = {
    'default': env.db(
        'DATABASE_URL',
        default='postgres://postgres:r1l2_postgre@postgres:5432/simple',
    )
}


# Password validation
# https://docs.djangoproject.com/en/3.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/3.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.2/howto/static-files/

STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATIC_URL = '/static/'

MEDIA_ROOT = os.path.join(BASE_DIR, 'bluebiulding', 'media')
MEDIA_URL = '/media/'

# Extra places for collectstatic to find static files.
STATICFILES_DIRS = (
    os.path.join(BASE_DIR, 'static'),
)


# Default primary key field type
# https://docs.djangoproject.com/en/3.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Redirect to home URL after login (Default redirects to /accounts/profile/)
LOGIN_REDIRECT_URL = '/control/dashboard/'