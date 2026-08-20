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


class SubscriptionBlockService:
    @staticmethod
    def block_expired_users():
        with transaction.atomic():
            now = timezone.now()
            subscriptions = (
                Subscription.objects.select_for_update()
                .filter(grace_end_date__lt=now)
                .exclude(status="BLOCKED")
            )

            for subscription in subscriptions:
                old_data = _snapshot(subscription)
                subscription.status = "BLOCKED"
                subscription.save()

                user = subscription.user
                user.is_active = False
                user.save(update_fields=["is_active", "updated_at"])

                JournalService.log_update(
                    user=user,
                    instance=subscription,
                    old_data=old_data,
                    new_data=_snapshot(subscription),
                )

            return subscriptions
