from django.utils.translation import gettext_lazy as _

from src.bases.views.imports import *
from src.bases.views.navigation import NavigationContextMixin


class BaseListView(NavigationContextMixin, LoginRequiredMixin, ListView):
    paginate_by = 20

    def _deny(self):
        messages.error(self.request, _("Sizga bu sahifaga kirish mumkin emas."))
        return redirect("dashboard")

    def get_branch(self):
        user = self.request.user

        if hasattr(user, "get_all_branches"):
            branches = user.get_all_branches()

            if branches:
                return branches[0]

        return None

    def has_permission(self):
        return True

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return super().dispatch(request, *args, **kwargs)
        if not self.has_permission():
            return self._deny()
        try:
            return super().dispatch(request, *args, **kwargs)
        except PermissionDenied:
            return self._deny()

    def _has_field(self, model, field_name):
        return any(field.name == field_name for field in model._meta.fields)

    def get_queryset(self):
        queryset = super().get_queryset()
        model = queryset.model

        if self._has_field(model, "is_deleted"):
            queryset = queryset.filter(is_deleted=False)

        user = self.request.user

        if hasattr(user, "get_all_branches") and self._has_field(model, "branch"):
            branches = user.get_all_branches()
            queryset = queryset.filter(branch__in=branches)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(self.get_navigation_context())
        return context
