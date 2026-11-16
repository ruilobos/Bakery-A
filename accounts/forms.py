"""The login forms' word on a throttled attempt (task 2.22, ADR-055)."""

import math

from django.contrib.auth.forms import AuthenticationForm
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.utils.translation import ngettext

from accounts.backends import refused_until


class ThrottleMessageMixin:
    """
    Say that sign-in is paused, and when to retry, for an attempt the throttle
    refused, rather than "wrong password": its password was never checked.
    """

    def get_invalid_login_error(self):
        reopens = refused_until(self.request)
        if reopens is None:
            return super().get_invalid_login_error()
        seconds = (reopens - timezone.now()).total_seconds()
        minutes = max(1, math.ceil(seconds / 60))
        message = ngettext(
            "Sign-in is paused after repeated failed attempts. "
            "Try again in %(minutes)d minute.",
            "Sign-in is paused after repeated failed attempts. "
            "Try again in %(minutes)d minutes.",
            minutes,
        )
        return ValidationError(message, code="throttled", params={"minutes": minutes})


class ThrottledAuthenticationForm(ThrottleMessageMixin, AuthenticationForm):
    """
    `/accounts/login/`'s form. Its template prints the form's own error, so the
    sentence it used to print for every error is this form's wrong-password one.
    """

    error_messages = {
        **AuthenticationForm.error_messages,
        "invalid_login": "Your username and password didn't match. Please try again.",
    }
