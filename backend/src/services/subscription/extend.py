from datetime import timedelta

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from src.core.models import Subscription, User as CustomUser
from src.services.journal import JournalService
from src.shared.json_utils import json_safe


def _snapshot(instance):
    data = {}
    for field in instance._meta.fields:
        value = getattr(instance, field.attname)
        data[field.attname] = json_safe(value)
    return data


class SubscriptionExtendService:
    @staticmethod
    def extend_subscription(subscription, duration_days, updated_by):
        with transaction.atomic():
            old_data = _snapshot(subscription)
            subscription.end_date = subscription.end_date + timedelta(days=duration_days)
            subscription.grace_end_date = subscription.end_date + timedelta(days=4)
            subscription.status = "ACTIVE"
            subscription.save()

            JournalService.log_update(
                user=updated_by,
                instance=subscription,
                old_data=old_data,
                new_data=_snapshot(subscription),
            )

            return subscription
