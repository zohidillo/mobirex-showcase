from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from src.core.models import Subscription, User as CustomUser
from src.services.journal import JournalService
from src.shared.json_utils import json_safe


def _snapshot(instance):
    data = {}
    for field in instance._meta.fields:
        value = getattr(instance, field.attname)
        data[field.attname] = json_safe(value)
    return data


class SubscriptionCheckService:
    @staticmethod
    def check_user_subscription(user):
        with transaction.atomic():
            if user.is_vip:
                return "ACTIVE"

            subscription = (
                Subscription.objects.select_for_update()
                .filter(user=user)
                .order_by("-end_date")
                .first()
            )
            if not subscription:
                raise ValidationError(_("Obuna topilmadi."))

            now = timezone.now()

            if now <= subscription.end_date:
                old_data = _snapshot(subscription)
                subscription.status = "ACTIVE"
                subscription.save()
                JournalService.log_update(
                    user=user,
                    instance=subscription,
                    old_data=old_data,
                    new_data=_snapshot(subscription),
                )
                return "ACTIVE"

            if subscription.end_date < now <= subscription.grace_end_date:
                old_data = _snapshot(subscription)
                subscription.status = "GRACE"
                subscription.save()
                JournalService.log_update(
                    user=user,
                    instance=subscription,
                    old_data=old_data,
                    new_data=_snapshot(subscription),
                )
                return "GRACE"

            old_data = _snapshot(subscription)
            subscription.status = "BLOCKED"
            subscription.save()
            user.is_active = False
            user.save(update_fields=["is_active", "updated_at"])
            JournalService.log_update(
                user=user,
                instance=subscription,
                old_data=old_data,
                new_data=_snapshot(subscription),
            )
            return "BLOCKED"
