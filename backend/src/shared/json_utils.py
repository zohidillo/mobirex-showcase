import json
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from django.db.models import Model, QuerySet
from django.utils.functional import Promise


def json_safe(value):
    """
    Returns JSON-serializable version of value.
    Handles lazy translations, datetime/date, Decimal, UUID, Model instances, QuerySets.
    Works recursively for dicts/lists/tuples/sets.
    """

    def _to_basic(obj):
        if obj is None:
            return None
        if isinstance(obj, Promise):
            return str(obj)
        if isinstance(obj, datetime):
            return obj.isoformat()
        if isinstance(obj, date):
            return obj.isoformat()
        if isinstance(obj, Decimal):
            return float(obj)
        if isinstance(obj, UUID):
            return str(obj)
        if isinstance(obj, bytes):
            return obj.decode("utf-8", errors="replace")
        if isinstance(obj, Model):
            return str(obj)
        if isinstance(obj, QuerySet):
            return [_to_basic(v) for v in obj]
        if isinstance(obj, dict):
            return {str(k): _to_basic(v) for k, v in obj.items()}
        if isinstance(obj, (list, tuple, set)):
            return [_to_basic(v) for v in obj]
        try:
            json.dumps(obj)
            return obj
        except TypeError:
            return str(obj)

    return _to_basic(value)
