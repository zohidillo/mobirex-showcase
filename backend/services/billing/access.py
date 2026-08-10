from dataclasses import dataclass

from django.utils.translation import gettext_lazy as _

from .grace_status import GraceStatusService


@dataclass
class AccessDecision:
    status: str
    is_allowed: bool
    warning_message: str = ""
    blocked_message: str = ""


class AccountAccessService:
    BLOCKED_MESSAGE = _("Siz to‘lov qilishingiz kerak. Hozirgi holatingiz bloklangan.")
    GRACE_MESSAGE = _("Balansingiz tugagan. 3 kun ichida hisobni to‘ldiring.")

    @classmethod
    def evaluate_user(cls, user, current_date=None, persist=False):
        status = GraceStatusService.sync_user_status(
            user,
            current_date=current_date,
            persist=persist,
        )
        if status == GraceStatusService.BLOCKED:
            return AccessDecision(
                status=status,
                is_allowed=False,
                blocked_message=str(cls.BLOCKED_MESSAGE),
            )
        if status == GraceStatusService.GRACE:
            return AccessDecision(
                status=status,
                is_allowed=True,
                warning_message=str(cls.GRACE_MESSAGE),
            )
        return AccessDecision(status=status, is_allowed=True)
