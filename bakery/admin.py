"""
The Django admin's site (tasks 2.15, 2.27, 2.28 and 19.4; ADR-019, ADR-052,
ADR-054, ADR-056).

Superuser-only support tooling: deliberately cross-tenant, and never linked from
the tenant UI. `django_admin_log` records its writes but not its reads, so each
page that shows a model's rows logs who opened it. That covers every model, not
only those the personal-data inventory names: `RawMaterial` shows a supplier's
name, and any model's history page shows the users in `django_admin_log`.

That table's rows go when their user goes, so each write is mirrored into the
stream too, where it outlives the account. A sign-in it refuses is logged too
(task 2.23), and a throttled one says when to retry (task 2.22).
"""

import json
from functools import wraps

from django.contrib import admin
from django.contrib.admin.forms import AdminAuthenticationForm
from django.contrib.admin.models import ADDITION, CHANGE, DELETION
from django.contrib.admin.utils import unquote
from django.core.exceptions import ValidationError
from django.http import Http404

from accounts.forms import ThrottleMessageMixin
from bakery.audit import failed_login, record

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


# Set on each `LogEntry` once it is mirrored, so `MirrorBulkDeletions` can tell
# which of the rows it is handed the receiver never saw.
MIRRORED = "_mirrored_to_audit"


def mirror(entry):
    """Copy one `LogEntry` into `bakery.audit`, and mark it as copied."""
    action = ACTIONS[entry.action_flag]
    model = entry.content_type.model_class()
    pk = model._meta.pk.to_python(entry.object_id)
    details = {"changed": changed_labels(entry)} if action == "update" else {}
    record(action, entry.user, model, pk, **details)
    setattr(entry, MIRRORED, True)


def mirror_admin_write(sender, instance, created, raw, **kwargs):
    """
    Mirror each `LogEntry` the admin saves, connected in `bakery/apps.py`.

    The admin logs a delete before it runs it, so `record`'s `on_commit` is what
    keeps a rolled-back write out of the stream. `delete_selected` runs outside a
    transaction, so if its delete fails the event stays, as Django's `LogEntry`
    does. A fixture's rows are `raw`: nobody made those writes here.

    Rows the admin writes with `bulk_create` send no `post_save`, so they reach
    the stream through `MirrorBulkDeletions` instead (ADR-056).
    """
    if created and not raw:
        mirror(instance)


class MirrorBulkDeletions:
    """
    Mirror the `LogEntry` rows `delete_selected` writes without a `post_save`.

    From Django 5.1, `log_deletions` logs two or more rows with `bulk_create`,
    which sends no signal, so the receiver never sees them. A row the receiver
    did see carries its mark, so none is mirrored twice, however many rows Django
    chooses to save one by one. `BakeryAdminSite.register` mixes this into every
    admin (ADR-056).
    """

    def log_deletions(self, request, queryset):
        entries = super().log_deletions(request, queryset)
        for entry in entries:
            if not getattr(entry, MIRRORED, False):
                mirror(entry)
        return entries


class AuditedAdminAuthenticationForm(ThrottleMessageMixin, AdminAuthenticationForm):
    """
    Log a non-staff account the admin turns away after its password matched.

    `authenticate()` has already succeeded by then, so `user_login_failed` never
    fires, yet nobody is signed in: it is a failed login all the same. A
    throttled attempt never got that far, and the mixin says when to retry.
    """

    def confirm_login_allowed(self, user):
        try:
            super().confirm_login_allowed(user)
        except ValidationError:
            failed_login(self.request, user.pk)
            raise


class BakeryAdminSite(admin.AdminSite):
    login_form = AuditedAdminAuthenticationForm

    def has_permission(self, request):
        return super().has_permission(request) and request.user.is_superuser

    def register(self, model_or_iterable, admin_class=None, **options):
        """
        Mix `MirrorBulkDeletions` into every admin registered here.

        That includes Django's own `GroupAdmin` and the re-registered `UserAdmin`,
        and a class added later cannot forget it, which is why 054 rejected a
        mixin written into each class by hand (ADR-056).
        """
        admin_class = admin_class or admin.ModelAdmin
        if not issubclass(admin_class, MirrorBulkDeletions):
            admin_class = type(
                admin_class.__name__,
                (MirrorBulkDeletions, admin_class),
                {
                    "__module__": admin_class.__module__,
                    "__qualname__": admin_class.__qualname__,
                },
            )
        super().register(model_or_iterable, admin_class, **options)

    def autocomplete_view(self, request):
        """
        Closed, since no page calls it (ADR-054).

        It answers from any admin's `search_fields`, so it returned usernames
        whether or not an admin declared `autocomplete_fields`, and `admin_view`
        logs only a `ModelAdmin`'s pages. The URL stays, so `admin:autocomplete`
        still reverses, and the permission check still runs first. Turning it
        back on means logging it first.
        """
        raise Http404

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
