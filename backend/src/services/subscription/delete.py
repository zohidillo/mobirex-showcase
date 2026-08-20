from django.db import transaction

from src.core.models import Subscription
from src.services.journal import JournalService
from src.shared.json_utils import json_safe


def _snapshot(instance):
    data = {}
    for field in instance._meta.fields:
        value = getattr(instance, field.attname)
        data[field.attname] = json_safe(value)
    return data


class SubscriptionDeleteService:
    @staticmethod
    def delete_subscription(subscription, deleted_by):
        with transaction.atomic():
            old_data = _snapshot(subscription)
            subscription.is_deleted = True
            subscription.save()
            JournalService.log_delete(
                user=deleted_by,
                instance=subscription,
                old_data=old_data,
            )
            return subscription
