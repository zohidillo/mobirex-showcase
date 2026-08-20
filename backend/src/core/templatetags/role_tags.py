from django import template

register = template.Library()


@register.filter
def has_role(user, role):
    if not user:
        return False
    if hasattr(user, "has_role"):
        return user.has_role(role)
    return getattr(user, "role", None) == role
