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


class SubscriptionCreateService:
    @staticmethod
    def create_subscription(user, plan_type, duration_days, created_by):
        with transaction.atomic():
            start_date = timezone.now()
            end_date = start_date + timedelta(days=duration_days)
            grace_end_date = end_date + timedelta(days=4)

            subscription = Subscription.objects.create(
                user=user,
                plan_type=plan_type,
                start_date=start_date,
                end_date=end_date,
                grace_end_date=grace_end_date,
                status="ACTIVE",
            )

            JournalService.log_create(
                user=created_by,
                instance=subscription,
                new_data=_snapshot(subscription),
            )

            return subscription
