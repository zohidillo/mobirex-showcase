from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

from src.shared.json_utils import json_safe


class StandardPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100
    page_query_param = "page"

    def get_paginated_data(self, data, *, extra_data=None):
        payload = {
            "count": self.page.paginator.count,
            "next": self.get_next_link(),
            "previous": self.get_previous_link(),
            "results": json_safe(data),
        }
        if extra_data:
            payload.update(json_safe(extra_data))
        return payload

    def get_paginated_response(self, data, *, extra_data=None):
        return Response(
            {
                "success": True,
                "data": self.get_paginated_data(data, extra_data=extra_data),
            }
        )
