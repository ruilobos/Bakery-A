from django.db import models


class LoginThrottle(models.Model):
    """
    Consecutive failed sign-ins on one submitted username (task 2.22, ADR-055).

    `key` is an HMAC of the username, never the username itself, so the table
    shows nobody's name and cannot tell a real account from an unknown one.
    `accounts.throttle` keeps the counts; a row goes on a successful sign-in, or
    a day after its last failure.
    """

    key = models.CharField(max_length=64, primary_key=True)
    failures = models.PositiveIntegerField(default=0)
    # Indexed for the sweep that forgets the keys a day old.
    last_failure = models.DateTimeField(db_index=True)
