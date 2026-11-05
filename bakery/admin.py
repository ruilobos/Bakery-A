"""
The Django admin's site (task 2.15, ADR-019, ADR-052).

Superuser-only support tooling: deliberately cross-tenant, and never linked from
the tenant UI. `django_admin_log` records its writes but not its reads, so each
page that shows a model's rows logs who opened it. That covers every model, not
only those the personal-data inventory names: `RawMaterial` shows a supplier's
name, and any model's history page shows the users in `django_admin_log`.
"""

from functools import wraps

from django.contrib import admin
from django.contrib.admin.utils import unquote

from bakery.audit import record


def target_pk(model, url_kwargs):
    # A list or add page names no row. The admin escapes a primary key in its
    # URLs, and `UserAdmin`'s password page calls that argument `id`.
    pk = url_kwargs.get("object_id", url_kwargs.get("id"))
    return None if pk is None else model._meta.pk.to_python(unquote(pk))


class BakeryAdminSite(admin.AdminSite):
    def has_permission(self, request):
        return super().has_permission(request) and request.user.is_superuser

    def admin_view(self, view, cacheable=False):
        """
        Log `admin_view` for each model page that renders.

        `super().admin_view` checks the permission before it calls `audited`, so
        a refused request logs nothing. A 200 is what separates a page that showed
        rows from a save's redirect, which `django_admin_log` already records, or
        a missing row's. The event omits the query string: a `?q=` search term can
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
