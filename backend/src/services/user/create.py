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


class UserCreateService:
    @staticmethod
    def create_user(validated_data, created_by):
        with transaction.atomic():
            data = dict(validated_data)
            password = data.pop("password", None)
            user = User(**data)
            user.is_active = True
            user.is_deleted = False
            user.account_status = (
                GraceStatusService.VIP if user.is_vip else GraceStatusService.ACTIVE
            )
            if user.is_vip:
                user.grace_start_date = None
            if password:
                user.set_password(password)
            user.save()
            JournalService.log_create(
                user=created_by,
                instance=user,
                new_data=_snapshot(user),
            )
            return user
