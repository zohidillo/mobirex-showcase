from src.bases.views.imports import *
from django.utils.translation import gettext_lazy as _
from src.bases.views.navigation import NavigationContextMixin


class BaseCreateView(NavigationContextMixin, LoginRequiredMixin, CreateView):
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

    def perform_create(self, form):
        return form.save()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(self.get_navigation_context())
        return context

    def form_valid(self, form):
        try:
            with transaction.atomic():
                self.object = self.perform_create(form)
        except Exception as exc:
            form.add_error(None, str(exc))
            messages.error(self.request, str(exc))
            return super(BaseCreateView, self).form_invalid(form)
        messages.success(self.request, _("Amal muvaffaqiyatli bajarildi."))
        return HttpResponseRedirect(self.get_success_url())

    def form_invalid(self, form):
        messages.error(self.request, _("Iltimos, xatolarni to‘g‘rilang."))
        return super().form_invalid(form)
