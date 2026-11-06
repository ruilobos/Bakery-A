"""
The Django admin's site (tasks 2.15 and 2.27, ADR-019, ADR-052, ADR-054).

Superuser-only support tooling: deliberately cross-tenant, and never linked from
the tenant UI. `django_admin_log` records its writes but not its reads, so each
page that shows a model's rows logs who opened it. That covers every model, not
only those the personal-data inventory names: `RawMaterial` shows a supplier's
name, and any model's history page shows the users in `django_admin_log`.

That table's rows go when their user goes, so each write is mirrored into the
stream too, where it outlives the account.
"""

import json
from functools import wraps

from django.contrib import admin
from django.contrib.admin.models import ADDITION, CHANGE, DELETION
from django.contrib.admin.utils import unquote

from bakery.audit import record

ACTIONS = {ADDITION: "create", CHANGE: "update", DELETION: "delete"}


def target_pk(model, url_kwargs):
    # A list or add page names no row. The admin escapes a primary key in its
    # URLs, and `UserAdmin`'s password page calls that argument `id`.
    pk = url_kwargs.get("object_id", url_kwargs.get("id"))
    return None if pk is None else model._meta.pk.to_python(unquote(pk))


def changed_labels(entry):
    # Only the `fields` lists: an inline's entry also holds `str(obj)`, a value.
    # They hold form labels, not the field names 2.9's events carry (ADR-054).
    # A `log_change` may pass plain text instead, which must not fail the write.
    message = entry.change_message
    labels = set()
    for change in json.loads(message) if message.startswith("[") else []:
        labels.update(change.get("changed", {}).get("fields", []))
    return sorted(labels)


def mirror_admin_write(sender, instance, created, raw, **kwargs):
    """
    Copy a new `LogEntry` into `bakery.audit`, connected in `bakery/apps.py`.

    The admin logs a delete before it runs it, so `record`'s `on_commit` is what
    keeps a rolled-back write out of the stream. `delete_selected` runs outside a
    transaction, so if its delete fails the event stays, as Django's `LogEntry`
    does. A fixture's rows are `raw`: nobody made those writes here.

    On Django 5.2, `delete_selected` logs two or more rows through `bulk_create`,
    which sends no `post_save`, so they would go unmirrored after 19.4.
    `test_delete_selected_logs_each_row` fails there rather than let that pass.
    """
    if not created or raw:
        return
    action = ACTIONS[instance.action_flag]
    model = instance.content_type.model_class()
    pk = model._meta.pk.to_python(instance.object_id)
    details = {"changed": changed_labels(instance)} if action == "update" else {}
    record(action, instance.user, model, pk, **details)


class BakeryAdminSite(admin.AdminSite):
    def has_permission(self, request):
        return super().has_permission(request) and request.user.is_superuser

    def admin_view(self, view, cacheable=False):
        """
        Log `admin_view` for each model page that renders.

        `super().admin_view` checks the permission before it calls `audited`, so
        a refused request logs nothing. A 200 is what separates a page that showed
        rows from a save's redirect, which `mirror_admin_write` already logs, or a
        missing row's. The event omits the query string: a `?q=` search term can
        be a person's name.
        """

        @wraps(view)
        def audited(request, *args, **kwargs):
            response = view(request, *args, **kwargs)
            model_admin = getattr(view, "__self__", None)
            if (
                isinstance(model_admin, admin.ModelAdmin)
                and response.status_code == 200
            ):
                model = model_admin.model
                pk = target_pk(model, kwargs)
                record("admin_view", request.user, model, pk)
            return response

        return super().admin_view(audited, cacheable)
