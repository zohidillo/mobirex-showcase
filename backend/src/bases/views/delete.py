from django.utils.translation import gettext_lazy as _

from src.bases.views.imports import *
from src.bases.views.navigation import NavigationContextMixin


class BaseDeleteView(NavigationContextMixin, LoginRequiredMixin, View):
    template_name = None
    pk_url_kwarg = "pk"

    def get_success_url(self):
        if hasattr(self, "success_url") and self.success_url:
            return self.success_url
        if hasattr(self, "success_url_name"):
            return reverse(self.success_url_name)
        model_name = self.model._meta.model_name
        return reverse(f"{model_name}_list")

    def _deny(self):
        messages.error(self.request, _("Sizga bu sahifaga kirish mumkin emas."))
        return redirect("dashboard")

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

    def get_branch(self):
        user = self.request.user
        if hasattr(user, "get_branch"):
            return user.get_branch()
        return getattr(user, "branch", None)

    def get_queryset(self):
        queryset = self.model._default_manager.all()
        if self._has_field(self.model, "is_deleted"):
            queryset = queryset.filter(is_deleted=False)
        branch = self.get_branch()
        if branch and self._has_field(self.model, "branch"):
            queryset = queryset.filter(branch=branch)
        return queryset

    def get_object(self):
        return get_object_or_404(self.get_queryset(), pk=self.kwargs.get(self.pk_url_kwarg, None))

    def perform_delete(self, obj):
        obj.is_deleted = True
        obj.save()

    def get_context_data(self, **kwargs):
        context = dict(kwargs)
        context.update(self.get_navigation_context())
        return context

    def get(self, request, *args, **kwargs):
        obj = self.get_object()
        if not self.template_name:
            raise PermissionDenied
        return render(request, self.template_name, self.get_context_data(object=obj))

    def post(self, request, *args, **kwargs):
        obj = self.get_object()
        with transaction.atomic():
            self.perform_delete(obj)
        messages.success(request, _("Amal muvaffaqiyatli bajarildi."))
        return redirect(self.get_success_url())

    def form_valid(self, form):
        messages.success(self.request, _("Amal muvaffaqiyatli bajarildi."))
        return redirect(self.get_success_url())

    def form_invalid(self, form):
        messages.error(self.request, _("Iltimos, xatolarni to‘g‘rilang."))
        return redirect(self.get_success_url())
