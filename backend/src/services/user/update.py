from django.db import transaction

from src.core.models import User
from src.services.billing import GraceStatusService
from src.services.journal import JournalService
from src.shared.json_utils import json_safe


def _snapshot(instance):
    data = {}
    for field in instance._meta.fields:
        value = getattr(instance, field.attname)
        data[field.attname] = json_safe(value)
    return data


class UserUpdateService:
    @staticmethod
    def update_user(user, validated_data, updated_by):
        with transaction.atomic():
            old_data = _snapshot(user)
            data = dict(validated_data)
            password = data.pop("password", None)
            for attr, value in data.items():
                setattr(user, attr, value)
            if user.is_vip:
                user.account_status = GraceStatusService.VIP
                user.grace_start_date = None
            elif user.account_status == GraceStatusService.VIP:
                user.account_status = GraceStatusService.resolve_status(user)
            if password:
                user.set_password(password)
            user.save()
            JournalService.log_update(
                user=updated_by,
                instance=user,
                old_data=old_data,
                new_data=_snapshot(user),
            )
            return user
