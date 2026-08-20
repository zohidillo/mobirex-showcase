"""API throttles."""

from rest_framework.throttling import SimpleRateThrottle, UserRateThrottle


class PinVerifyThrottle(UserRateThrottle):
    """Rate-limit PIN verification attempts per authenticated user."""

    scope = "pin_verify"


class PublicContactHourThrottle(SimpleRateThrottle):
    """Rate-limit the public contact form: 3/hour per IP.

    The endpoint is unauthenticated and open to the world, so the key is the
    client IP. Paired with ``PublicContactDayThrottle`` — DRF allows one rate
    per throttle class, and this surface needs both a burst and a daily cap.
    """

    scope = "public_contact_hour"

    def get_cache_key(self, request, view):
        return self.cache_format % {
            "scope": self.scope,
            "ident": self.get_ident(request),
        }


class PublicContactDayThrottle(SimpleRateThrottle):
    """Rate-limit the public contact form: 10/day per IP."""

    scope = "public_contact_day"

    def get_cache_key(self, request, view):
        return self.cache_format % {
            "scope": self.scope,
            "ident": self.get_ident(request),
        }


class LandingFormThrottle(SimpleRateThrottle):
    """Rate-limit landing site form submissions: 5/hour per IP.

    Only applies to anonymous callers that include X-Key header.
    Authenticated users and callers without X-Key are skipped.
    """

    scope = "landing_form"

    def get_cache_key(self, request, view):
        if request.user and request.user.is_authenticated:
            return None
        if not request.headers.get("X-Key"):
            return None
        return self.cache_format % {
            "scope": self.scope,
            "ident": self.get_ident(request),
        }
