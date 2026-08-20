from datetime import timedelta

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from src.core.models import SubscriptionPayment, Subscription
from src.services.journal import JournalService
from src.services.subscription import SubscriptionCreateService, SubscriptionExtendService, SubscriptionCheckService
from src.shared.json_utils import json_safe


_DURATION_DAYS = {
    "MONTHLY": 30,
    "YEARLY": 365,
}


def _snapshot(instance):
    data = {}
    for field in instance._meta.fields:
        value = getattr(instance, field.attname)
        data[field.attname] = json_safe(value)
    return data


def _duration_for(period_type):
    days = _DURATION_DAYS.get(period_type)
    if not days:
        raise ValidationError(_("Noto‘g‘ri davr turi."))
    return days


class SubscriptionPaymentService:
    @staticmethod
    def create_payment(validated_data, created_by):
        with transaction.atomic():
            data = dict(validated_data)
            user = data["user"]
            period_type = data["period_type"]

            duration_days = _duration_for(period_type)

            subscription = (
                Subscription.objects.select_for_update()
                .filter(user=user, is_deleted=False)
                .order_by("-end_date")
                .first()
            )
            if subscription:
                SubscriptionExtendService.extend_subscription(
                    subscription,
                    duration_days=duration_days,
                    updated_by=created_by,
                )
            else:
                subscription = SubscriptionCreateService.create_subscription(
                    user=user,
                    plan_type=period_type,
                    duration_days=duration_days,
                    created_by=created_by,
                )
            if subscription.status != "ACTIVE":
                subscription.status = "ACTIVE"
                subscription.save(update_fields=["status", "updated_at"])

            payment = SubscriptionPayment.objects.create(
                user=user,
                subscription=subscription,
                amount=data["amount"],
                period_type=period_type,
                paid_at=timezone.now(),
                added_by=created_by,
                note=data.get("note"),
            )

            JournalService.log_create(
                user=created_by,
                instance=payment,
                new_data=_snapshot(payment),
            )

            return payment

    @staticmethod
    def update_payment(payment, validated_data, updated_by):
        with transaction.atomic():
            old_data = _snapshot(payment)
            old_period = payment.period_type
            new_period = validated_data.get("period_type", old_period)

            if new_period != old_period:
                old_days = _duration_for(old_period)
                new_days = _duration_for(new_period)
                difference = new_days - old_days

                subscription = payment.subscription
                if not subscription:
                    raise ValidationError(_("Ushbu to‘lov uchun obuna topilmadi."))

                if difference > 0:
                    SubscriptionExtendService.extend_subscription(
                        subscription,
                        duration_days=difference,
                        updated_by=updated_by,
                    )
                elif difference < 0:
                    sub_old_data = _snapshot(subscription)
                    subscription.end_date = subscription.end_date + timedelta(days=difference)
                    subscription.grace_end_date = subscription.end_date + timedelta(days=4)
                    subscription.save()
                    JournalService.log_update(
                        user=updated_by,
                        instance=subscription,
                        old_data=sub_old_data,
                        new_data=_snapshot(subscription),
                    )
                    SubscriptionCheckService.check_user_subscription(subscription.user)

            for attr, value in validated_data.items():
                setattr(payment, attr, value)
            payment.save()

            JournalService.log_update(
                user=updated_by,
                instance=payment,
                old_data=old_data,
                new_data=_snapshot(payment),
            )

            return payment

    @staticmethod
    def delete_payment(payment, deleted_by):
        with transaction.atomic():
            old_data = _snapshot(payment)

            subscription = payment.subscription
            if not subscription:
                raise ValidationError(_("Ushbu to‘lov uchun obuna topilmadi."))

            days = _duration_for(payment.period_type)
            sub_old_data = _snapshot(subscription)
            subscription.end_date = subscription.end_date - timedelta(days=days)
            subscription.grace_end_date = subscription.end_date + timedelta(days=4)
            subscription.save()
            JournalService.log_update(
                user=deleted_by,
                instance=subscription,
                old_data=sub_old_data,
                new_data=_snapshot(subscription),
            )
            SubscriptionCheckService.check_user_subscription(subscription.user)

            payment.is_deleted = True
            payment.save()

            JournalService.log_delete(
                user=deleted_by,
                instance=payment,
                old_data=old_data,
            )

            return payment
