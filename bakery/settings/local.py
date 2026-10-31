"""
Local development settings (ADR-028).

`base.py` is production; this module opts *into* the conveniences that are unsafe
there. Nothing here is ever loaded outside a developer's machine.

Use it explicitly — `manage.py` defaults to `base`, deliberately, so a forgotten
setting leaves you in the safe configuration rather than a permissive one:

    # PowerShell
    $env:DJANGO_SETTINGS_MODULE = "bakery.settings.local"; python manage.py runserver

    # bash
    DJANGO_SETTINGS_MODULE=bakery.settings.local python manage.py runserver

Task 1.12 replaces that with a one-command launcher.
"""

from bakery.settings.base import *

DEBUG = True

ALLOWED_HOSTS = ["localhost", "127.0.0.1", "[::1]"]

# Fixed here rather than read like base.py's (task 2.3), so a `.env` holding a
# host's values cannot break login on localhost.
CSRF_TRUSTED_ORIGINS = []
SESSION_COOKIE_DOMAIN = None
CSRF_COOKIE_DOMAIN = None

# The local database is the postgres:17 container (ADR-026 pins the major
# version across every environment), reached through `.env`'s DATABASE_URL:
# copy `.env.example`.
