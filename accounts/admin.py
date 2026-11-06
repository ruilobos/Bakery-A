"""
The admin's `User` page (task 2.27, ADR-054).

Until roadmap 11.9 sets the erasure strategy, an account is deactivated, not
deleted: the audit stream names actors by id, so the row has to stay for an id to
mean anyone. `UserAdmin`'s `is_active` box does that, and already stops the sign-in.
"""

from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin

User = get_user_model()

admin.site.unregister(User)


@admin.register(User)
class AccountAdmin(UserAdmin):
    def has_delete_permission(self, request, obj=None):
        return False
