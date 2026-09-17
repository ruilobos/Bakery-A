"""
Test settings (ADR-028).

Deliberately minimal. There is no test suite yet — task **6.23** adopts
`pytest` + `pytest-django` + `pytest-cov` and owns extending this module, so it
holds only what is true regardless of runner rather than guessing at pytest's
needs in advance.

    DJANGO_SETTINGS_MODULE=bakery.settings.test python manage.py test
"""
from bakery.settings.base import *  # noqa: F401,F403

# Tests must never depend on DEBUG-only behaviour: DEBUG changes error handling,
# template rendering and static file serving, so a suite that passes only under
# DEBUG is testing a configuration nothing ships.
DEBUG = False

ALLOWED_HOSTS = ['testserver', 'localhost', '127.0.0.1']

# The default PBKDF2 hasher dominates the runtime of any test that logs a user in.
PASSWORD_HASHERS = ['django.contrib.auth.hashers.MD5PasswordHasher']

# Static files are not the subject of these tests, and the manifest storage in
# base.py would require `collectstatic` to have run first.
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'
