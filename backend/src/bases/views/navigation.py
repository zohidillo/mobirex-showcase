from src.shared.navigation import get_back_url, should_show_back_button


class NavigationContextMixin:
    def get_navigation_context(self):
        request = getattr(self, "request", None)
        if request is None:
            return {
                "show_back_button": False,
                "back_url": "",
            }

        show_back_button = should_show_back_button(request)
        return {
            "show_back_button": show_back_button,
            "back_url": get_back_url(request) if show_back_button else "",
        }

