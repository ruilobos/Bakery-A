"""
The one authentication backend (task 2.22, ADR-055; ADR-028 clause 4).

Both `/accounts/login/` and `/admin/login/` call `authenticate()`, so this one
backend throttles both. 2.20's capability backend builds on it rather than
beside it: a second password backend listed first would bypass the throttle,
and one listed after it would check every wrong password twice.
"""

from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.core.exceptions import PermissionDenied

from accounts import throttle

# Where the backend leaves a refusal on the request, for the login form to say
# when to retry and for 2.23's receiver to log it as `login_throttled`. Django
# fires `user_login_failed` for a refused attempt too.
REFUSED_UNTIL = "login_refused_until"


def refused_until(request):
    """When sign-in reopens, if the throttle refused this request's attempt."""
    return getattr(request, REFUSED_UNTIL, None)


class ThrottledModelBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        """
        Refuse an attempt inside its username's window, before the password.

        A refusal raises `PermissionDenied` without hashing the password, so a
        right password tried inside the window tells the guesser nothing. With
        no request to mark, as from the test client's `login()`, the attempt is
        refused all the same, and logged as an ordinary `login_failed`.
        """
        if username is None:
            username = kwargs.get(get_user_model().USERNAME_FIELD)
        if username is None or password is None:
            return None
        reopens = throttle.count_attempt(username)
        if reopens is not None:
            if request is not None:
                setattr(request, REFUSED_UNTIL, reopens)
            raise PermissionDenied
        user = super().authenticate(request, username, password, **kwargs)
        if user is not None:
            throttle.clear(username)
        return user
