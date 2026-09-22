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
from bakery.settings.base import *  # noqa: F401,F403

DEBUG = True

ALLOWED_HOSTS = ['localhost', '127.0.0.1', '[::1]']

# The local database is the postgres:17 container (ADR-026 pins the major
# version across every environment). Override with DATABASE_URL if yours differs.
