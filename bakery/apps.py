from django.contrib.admin.apps import AdminConfig


class BakeryAdminConfig(AdminConfig):
    """Replace the default `admin.site`, so every `admin.site.register` uses it."""

    default_site = "bakery.admin.BakeryAdminSite"
