"""
The login throttle's counts (task 2.22, ADR-055).

Each submitted username is counted under its HMAC. Five consecutive failures go
free; from the fifth on, each failure opens a window, 1 minute doubling to at
most 15, in which every attempt is refused. A refused attempt is not counted and
does not extend its window. A success clears the key, and a key with no failure
for a day is forgotten. There is no IP address until 2.24 settles the proxy.
"""

from datetime import timedelta

from django.db import transaction
from django.utils import timezone
from django.utils.crypto import salted_hmac

from accounts.models import LoginThrottle

FREE_FAILURES = 5
FIRST_WINDOW = timedelta(minutes=1)
LONGEST_WINDOW = timedelta(minutes=15)
# Doublings past the fifth failure that reach LONGEST_WINDOW (1 min × 2⁴ > 15).
# Capping the exponent keeps a long run of failures from overflowing timedelta.
DOUBLINGS = 4
FORGET_AFTER = timedelta(days=1)


def key_for(username):
    # The username as the backend receives it: an unknown one is keyed exactly
    # as a real one is, so the table never shows which accounts exist.
    return salted_hmac("accounts.throttle", username, algorithm="sha256").hexdigest()


def reopens_at(failures, last_failure):
    """When sign-in reopens after `failures` consecutive failures, or None."""
    if failures < FREE_FAILURES:
        return None
    doublings = min(failures - FREE_FAILURES, DOUBLINGS)
    return last_failure + min(FIRST_WINDOW * 2**doublings, LONGEST_WINDOW)


def count_attempt(username):
    """
    Count an attempt on `username` before its password is checked.

    Return when sign-in reopens if the attempt falls inside a window, having
    written nothing; otherwise count it as a failure, which a success then
    clears, and return None.

    The count is taken under the key's row lock, so a parallel burst of guesses
    is counted rather than racing between a read and a write. It commits before
    the password is hashed, so the lock is not held while it is. Expired keys
    are swept after that commit, holding no other lock: two attempts that each
    held their own key while sweeping the other's would deadlock.
    """
    now = timezone.now()
    expired = now - FORGET_AFTER
    with transaction.atomic():
        row, _ = LoginThrottle.objects.select_for_update().get_or_create(
            key=key_for(username), defaults={"last_failure": now}
        )
        if row.last_failure <= expired:
            row.failures = 0
        reopens = reopens_at(row.failures, row.last_failure)
        if reopens is not None and reopens > now:
            return reopens
        row.failures += 1
        row.last_failure = now
        row.save()
    LoginThrottle.objects.filter(last_failure__lte=expired).delete()
    return None


def clear(username):
    """Forget `username`'s failures once its password has matched."""
    LoginThrottle.objects.filter(key=key_for(username)).delete()
