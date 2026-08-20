from django import template

register = template.Library()


@register.simple_tag
def querystring(request_get, **kwargs):
    params = request_get.copy()
    for key, value in kwargs.items():
        if value is None or value == "":
            params.pop(key, None)
        else:
            params[key] = value
    return params.urlencode()


@register.simple_tag
def pagination_range(page_obj, paginator, delta=2):
    current = page_obj.number
    total = paginator.num_pages

    if total <= (delta * 2 + 5):
        return list(range(1, total + 1))

    pages = [1]
    start = max(2, current - delta)
    end = min(total - 1, current + delta)

    if start > 2:
        pages.append(None)

    pages.extend(range(start, end + 1))

    if end < total - 1:
        pages.append(None)

    pages.append(total)
    return pages
