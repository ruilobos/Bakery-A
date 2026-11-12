"""
Audit events (ADR-052).

Each event is one JSON object, logged as one line on the ``bakery.audit``
logger, which ``settings/base.py`` sends to stdout. An event names its actor and
its target by primary key and never carries a field's value. It is logged once
the write has committed, so a write that fails or rolls back leaves no event.
A refused sign-in writes nothing, so it is logged at once.
"""

import json
import logging

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.db import transaction
from django.utils import timezone

logger = logging.getLogger(__name__)


def record(action, actor, model, pk, *, on_commit=True, **details):
    # An anonymous user's pk is None, which is how an event says "anonymous".
    event = {
        "action": action,
        "actor": actor.pk,
        "at": timezone.now().isoformat(),
        "target": {"model": model._meta.label_lower, "pk": pk},
        **details,
    }
    line = json.dumps(event, default=str)
    if on_commit:
        transaction.on_commit(lambda: logger.info(line))
    else:
        logger.info(line)


def log_login(sender, request, user, **kwargs):
    """Log `login` once Django's `login()` has signed `user` in (task 2.23)."""
    record("login", user, user, user.pk)


def log_failed_login(sender, credentials, request=None, **kwargs):
    """
    Log `login_failed` for each attempt `authenticate()` rejects (task 2.23).

    `credentials` is what was submitted, its password already masked. Only the
    username is read, to find the account's id; nothing else from it reaches the
    event.
    """
    User = get_user_model()
    username = credentials.get(User.USERNAME_FIELD, credentials.get("username"))
    accounts = User._default_manager.filter(**{User.USERNAME_FIELD: username})
    failed_login(request, accounts.values_list("pk", flat=True).first(), username)


def failed_login(request, pk, username=None):
    """
    Log a refused sign-in against the account `pk`, or `None` when none matched.

    It is logged at once rather than on commit: nothing was written, and an
    attempt must stay on record even if the request's transaction rolls back. The
    actor is whoever was already signed in, usually nobody. Only an unknown
    account is named by its username, since no id exists (ADR-052).
    """
    actor = getattr(request, "user", AnonymousUser())
    details = {"username": username} if pk is None else {}
    record("login_failed", actor, get_user_model(), pk, on_commit=False, **details)


class AuditedSaveMixin:
    """Log `create` or `update` once a CreateView or UpdateView has saved."""

    def form_valid(self, form):
        # CreateView starts with no object; UpdateView has already fetched one.
        action = "create" if self.object is None else "update"
        response = super().form_valid(form)
        details = {"changed": sorted(form.changed_data)} if action == "update" else {}
        record(action, self.request.user, self.object, self.object.pk, **details)
        return response


class AuditedDeleteMixin:
    """
    Log `delete` once a DeleteView has deleted its object.

    It wraps `post`, not `delete()`: from Django 4.0, DeleteView deletes in
    `form_valid()` and never calls `delete()`, so an override there goes silent
    after Epic 19's upgrade.
    """

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        # Model.delete() sets obj.pk to None, so keep it while it still exists.
        self.audit_pk = obj.pk
        return obj

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        record("delete", request.user, self.object, self.audit_pk)
        return response
