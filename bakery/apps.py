from django.contrib.admin.apps import AdminConfig
from django.db.models.signals import post_save


class BakeryAdminConfig(AdminConfig):
    """Replace the default `admin.site`, so every `admin.site.register` uses it."""

    default_site = "bakery.admin.BakeryAdminSite"

    def ready(self):
        super().ready()
        # Not at the top: bakery.admin imports models, which need the app registry.
        from bakery.admin import mirror_admin_write

        post_save.connect(mirror_admin_write, sender="admin.LogEntry")
