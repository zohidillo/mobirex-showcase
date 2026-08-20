from django.utils import timezone


class GraceStatusService:
    ACTIVE = "active"
    GRACE = "grace"
    BLOCKED = "blocked"
    VIP = "vip"
    GRACE_DAYS = 3

    @classmethod
    def today(cls, current_date=None):
        if current_date is not None:
            return current_date
        return timezone.localdate()

    @classmethod
    def resolve_status(cls, user, current_date=None):
        current_date = cls.today(current_date)

        if getattr(user, "is_vip", False) or getattr(user, "account_status", None) == cls.VIP:
            return cls.VIP

        balance = getattr(user, "balance", None) or 0
        if balance < 0:
            grace_start_date = getattr(user, "grace_start_date", None) or current_date
            if (current_date - grace_start_date).days >= cls.GRACE_DAYS:
                return cls.BLOCKED
            return cls.GRACE

        return cls.ACTIVE

    @classmethod
    def grace_days_left(cls, user, current_date=None):
        """Return remaining grace days, or ``None`` when not in grace.

        Display-only helper (no billing math changed): counts down from
        ``grace_start_date`` over ``GRACE_DAYS``. Clamped at 0.
        """
        grace_start_date = getattr(user, "grace_start_date", None)
        if grace_start_date is None:
            return None
        current_date = cls.today(current_date)
        used_days = (current_date - grace_start_date).days
        return max(0, cls.GRACE_DAYS - used_days)

    @classmethod
    def sync_user_status(cls, user, current_date=None, persist=False):
        current_date = cls.today(current_date)
        desired_status = cls.resolve_status(user, current_date=current_date)
        update_fields = []

        if desired_status == cls.VIP:
            if user.account_status != cls.VIP:
                user.account_status = cls.VIP
                update_fields.append("account_status")
            if user.grace_start_date is not None:
                user.grace_start_date = None
                update_fields.append("grace_start_date")
        elif desired_status == cls.ACTIVE:
            if user.account_status != cls.ACTIVE:
                user.account_status = cls.ACTIVE
                update_fields.append("account_status")
            if user.grace_start_date is not None:
                user.grace_start_date = None
                update_fields.append("grace_start_date")
        elif desired_status == cls.GRACE:
            if user.grace_start_date is None:
                user.grace_start_date = current_date
                update_fields.append("grace_start_date")
            if user.account_status != cls.GRACE:
                user.account_status = cls.GRACE
                update_fields.append("account_status")
        elif user.account_status != cls.BLOCKED:
            user.account_status = cls.BLOCKED
            update_fields.append("account_status")

        if persist and update_fields:
            user.save(update_fields=list(dict.fromkeys(update_fields + ["updated_at"])))

        return desired_status
