from django.apps import AppConfig


class AccountsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "accounts"

    def ready(self):
        # Every sign-in goes through Django's `authenticate()` and `login()`, so
        # their signals cover `/accounts/login/` and the admin's alike (task 2.23).
        # Imported here: bakery.audit imports auth's models, which need the
        # app registry.
        from django.contrib.auth.signals import user_logged_in, user_login_failed

        from bakery.audit import log_failed_login, log_login

        user_logged_in.connect(log_login)
        user_login_failed.connect(log_failed_login)
