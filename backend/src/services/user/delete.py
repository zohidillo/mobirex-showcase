from django.db import transaction
from django.utils import timezone

from src.core.models import User
from src.services.journal import JournalService
from src.shared.json_utils import json_safe


def _snapshot(instance):
    data = {}
    for field in instance._meta.fields:
        value = getattr(instance, field.attname)
        data[field.attname] = json_safe(value)
    return data


def _build_deleted_username(original):
    """Return a free `<original>-deleted[-N]` username (globally unique)."""
    base = f"{original}-deleted"
    candidate = base
    counter = 1
    # `User.objects` (CustomUserManager) does not filter is_deleted, so this
    # checks every row — username has a global unique constraint.
    while User.objects.filter(username=candidate).exists():
        candidate = f"{base}-{counter}"
        counter += 1
    return candidate


class UserDeleteService:
    @staticmethod
    def delete_user(user, deleted_by):
        with transaction.atomic():
            old_data = _snapshot(user)
            user.is_deleted = True
            user.save()
            JournalService.log_delete(
                user=deleted_by,
                instance=user,
                old_data=old_data,
            )
            return user

    @staticmethod
    def soft_delete_account(user):
        """Self-service soft delete: rename, deactivate, mark deleted.

        Only the four account fields are touched. Business records (debts,
        sales, phones, capital, branch links) are intentionally left intact.
        """
        with transaction.atomic():
            locked = User.objects.select_for_update().get(pk=user.pk)
            old_data = _snapshot(locked)

            locked.username = _build_deleted_username(locked.username)
            locked.is_deleted = True
            locked.is_active = False
            locked.deleted_at = timezone.now()
            locked.save(
                update_fields=["username", "is_deleted", "is_active", "deleted_at", "updated_at"]
            )

            JournalService.log_update(
                user=locked,
                instance=locked,
                old_data=old_data,
                new_data=_snapshot(locked),
            )
            return locked
