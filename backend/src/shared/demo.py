"""Restrictions for demo (app-review) accounts.

Demo accounts are shared, read-only-ish review logins. They must not be able to
lock themselves out or mutate their own credentials, otherwise the next reviewer
can no longer sign in. The message is intentionally kept in English because it is
shown to store reviewers.
"""

from rest_framework.exceptions import PermissionDenied


DEMO_ACTION_BLOCKED_MESSAGE = "This action is disabled for the demo account."


def is_demo_user(user):
    """Return whether the given user is one of the demo/review accounts."""
    return bool(
        user
        and getattr(user, "is_authenticated", False)
        and getattr(user, "is_demo", False)
    )


def block_demo_user(user):
    """Raise a 403 PermissionDenied when a demo account tries a restricted action."""
    if is_demo_user(user):
        raise PermissionDenied(DEMO_ACTION_BLOCKED_MESSAGE)
