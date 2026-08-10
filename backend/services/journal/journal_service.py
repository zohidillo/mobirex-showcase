from django.db import transaction
from django.utils import timezone

from src.core.models import Journal
from src.shared.json_utils import json_safe


def _instance_to_dict(instance):
    data = {}
    for field in instance._meta.fields:
        value = getattr(instance, field.attname)
        data[field.attname] = json_safe(value)
    return data


def _ensure_data(instance, data):
    if data is None and instance is not None:
        return _instance_to_dict(instance)
    return json_safe(data)


class JournalService:
    @staticmethod
    def log_create(*, user, instance, new_data=None):
        with transaction.atomic():
            new_data = _ensure_data(instance, new_data)
            Journal.objects.create(
                user=user,
                action="CREATE",
                model_name=instance._meta.model_name,
                object_id=instance.pk,
                object_repr=str(instance),
                branch=getattr(instance, "branch", None),
                old_data=None,
                new_data=new_data,
            )

    @staticmethod
    def log_update(*, user, instance, old_data, new_data):
        with transaction.atomic():
            old_data = _ensure_data(instance, old_data)
            new_data = _ensure_data(instance, new_data)
            Journal.objects.create(
                user=user,
                action="UPDATE",
                model_name=instance._meta.model_name,
                object_id=instance.pk,
                object_repr=str(instance),
                branch=getattr(instance, "branch", None),
                old_data=old_data,
                new_data=new_data,
            )

    @staticmethod
    def log_delete(*, user, instance, old_data):
        with transaction.atomic():
            old_data = _ensure_data(instance, old_data)
            Journal.objects.create(
                user=user,
                action="DELETE",
                model_name=instance._meta.model_name,
                object_id=instance.pk,
                object_repr=str(instance),
                branch=getattr(instance, "branch", None),
                old_data=old_data,
                new_data=None,
            )

    @staticmethod
    def log_custom(
        *,
        user,
        model_name,
        object_id,
        action,
        old_data=None,
        new_data=None,
        object_repr=None,
        branch=None,
    ):
        with transaction.atomic():
            Journal.objects.create(
                user=user,
                action=action,
                model_name=model_name,
                object_id=object_id,
                object_repr=object_repr,
                branch=branch,
                old_data=json_safe(old_data),
                new_data=json_safe(new_data),
            )
