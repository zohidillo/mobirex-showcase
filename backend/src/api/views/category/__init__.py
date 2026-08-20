"""Category API views."""

from .accessory import AccessoryCategoryListAPIView
from .phone import PhoneCategoryListAPIView

__all__ = [
    "AccessoryCategoryListAPIView",
    "PhoneCategoryListAPIView",
]
