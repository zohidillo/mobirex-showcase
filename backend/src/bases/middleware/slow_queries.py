import logging
import time

from django.db import connection


logger = logging.getLogger("django.db.slow")


class SlowQueryLoggingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        def wrapper(execute, sql, params, many, context):
            start = time.monotonic()
            try:
                return execute(sql, params, many, context)
            finally:
                duration_ms = (time.monotonic() - start) * 1000
                if duration_ms >= 500:
                    logger.warning("Slow query (%.1f ms): %s", duration_ms, sql)

        with connection.execute_wrapper(wrapper):
            return self.get_response(request)
