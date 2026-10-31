"""
Test settings (ADR-028).

Deliberately minimal. There is no test suite yet — task **6.23** adopts
`pytest` + `pytest-django` + `pytest-cov` and owns extending this module, so it
holds only what is true regardless of runner rather than guessing at pytest's
needs in advance.

    DJANGO_SETTINGS_MODULE=bakery.settings.test python manage.py test
"""

from bakery.settings.base import *

# Tests must never depend on DEBUG-only behaviour: DEBUG changes error handling,
# template rendering and static file serving, so a suite that passes only under
# DEBUG is testing a configuration nothing ships.
DEBUG = False

ALLOWED_HOSTS = ["testserver", "localhost", "127.0.0.1"]

# Fixed here rather than read like base.py's (task 2.3), so a developer's `.env`
# cannot change what the suite tests.
CSRF_TRUSTED_ORIGINS = []
SESSION_COOKIE_DOMAIN = None
CSRF_COOKIE_DOMAIN = None

# The test client speaks plain HTTP, so base.py's redirect (task 2.4) would answer
# every request with a 301. The rest stays production's, fixed so `.env` cannot opt
# the suite out: the client ignores the Secure flag, and Django sends HSTS over
# HTTPS only.
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000

# The default PBKDF2 hasher dominates the runtime of any test that logs a user in.
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

# Static files are not the subject of these tests, and the manifest storage in
# base.py would require `collectstatic` to have run first.
STATICFILES_STORAGE = "django.contrib.staticfiles.storage.StaticFilesStorage"
