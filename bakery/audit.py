"""
Audit events (ADR-052).

Each event is one JSON object, logged as one line on the ``bakery.audit``
logger, which ``settings/base.py`` sends to stdout. An event names its actor and
its target by primary key and never carries a field's value. It is logged once
the write has committed, so a write that fails or rolls back leaves no event.
"""

import json
import logging

from django.db import transaction
from django.utils import timezone

logger = logging.getLogger(__name__)


def record(action, actor, model, pk, **details):
    # An anonymous user's pk is None, which is how an event says "anonymous".
    event = {
        "action": action,
        "actor": actor.pk,
        "at": timezone.now().isoformat(),
        "target": {"model": model._meta.label_lower, "pk": pk},
        **details,
    }
    line = json.dumps(event, default=str)
    transaction.on_commit(lambda: logger.info(line))


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
