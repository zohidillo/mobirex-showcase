from datetime import date
from types import SimpleNamespace

from django import forms as django_forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from src.bases.views import *
from src.services.capital import CapitalService
from src.shared.filters import get_request_year_month


_MONTH_NAMES = {
    1: _("yanvar"),
    2: _("fevral"),
    3: _("mart"),
    4: _("aprel"),
    5: _("may"),
    6: _("iyun"),
    7: _("iyul"),
    8: _("avgust"),
    9: _("sentabr"),
    10: _("oktabr"),
    11: _("noyabr"),
    12: _("dekabr"),
}

MONTH_CHOICES = [(str(i), _MONTH_NAMES[i]) for i in range(1, 13)]


class PhoneCapitalUpdateForm(django_forms.ModelForm):
    month = django_forms.ChoiceField(choices=MONTH_CHOICES)
    year = django_forms.ChoiceField(choices=[])

    class Meta:
        model = models.PhoneCapital
        fields = [
            "branch",
            "invested_amount",
        ]

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        self.allow_existing = kwargs.pop("allow_existing", False)
        super().__init__(*args, **kwargs)
        if user and user.has_role("OWNER"):
            branches = user.get_all_branches("OWNER")
            if not branches:
                branches = list(models.Branch.objects.filter(owner=user))
            self.fields["branch"].queryset = models.Branch.objects.filter(
                id__in=[b.id for b in branches]
            )
            self.fields["branch"].required = True
        else:
            self.fields["branch"].queryset = models.Branch.objects.none()
            self.fields["branch"].disabled = True
            self.fields["branch"].widget = django_forms.HiddenInput()

        instance = getattr(self, "instance", None)
        if instance and instance.pk and instance.month:
            self.initial.setdefault("month", str(instance.month.month))
            self.initial.setdefault("year", str(instance.month.year))
            if instance.branch:
                self.initial.setdefault("branch", instance.branch_id)

        self.fields["year"].choices = self._get_year_choices(user, instance)

    def _get_year_choices(self, user, instance):
        years = {timezone.localtime().year}
        if instance and instance.month:
            years.add(instance.month.year)
        qs = models.PhoneCapital.objects.none()
        if user and user.has_role("OWNER"):
            branches = user.get_all_branches("OWNER")
            if branches:
                qs = models.PhoneCapital.objects.filter(branch__in=branches, is_deleted=False)
        if qs.exists():
            years.update({dt.year for dt in qs.dates("month", "year")})
        year_list = sorted(years)
        return [(str(y), str(y)) for y in year_list]

    def clean(self):
        cleaned = super().clean()
        month = cleaned.get("month")
        year = cleaned.get("year")
        branch = cleaned.get("branch")
        if not month or not year or not branch:
            return cleaned

        try:
            month_int = int(month)
            year_int = int(year)
            month_start = date(year_int, month_int, 1)
        except (TypeError, ValueError):
            raise ValidationError(_("Oy yoki yil noto‘g‘ri."))

        if not self.allow_existing:
            existing = models.PhoneCapital.objects.filter(branch=branch, month=month_start)
            if self.instance and self.instance.pk:
                existing = existing.exclude(pk=self.instance.pk)
            if existing.exists():
                self.add_error("month", _("Ushbu filial va oy uchun kapital allaqachon mavjud."))

        cleaned["month_start"] = month_start
        return cleaned


class PhoneCapitalListView(BaseListView):
    model = models.PhoneCapital
    template_name = "phone_capital/list.html"
    paginate_by = 20

    def has_permission(self):
        return self.request.user.has_role("OWNER")

    def get_queryset(self):
        user = self.request.user
        branches = user.get_all_branches("OWNER")
        if not branches:
            return []
        base_qs = (
            models.PhoneCapital.objects.filter(branch__in=branches, is_deleted=False)
            .select_related("branch")
        )
        month_start = timezone.localtime().date().replace(day=1)
        existing_branch_ids = set(
            base_qs.filter(month=month_start).values_list("branch_id", flat=True)
        )
        placeholders = []
        for branch in branches:
            if branch.id in existing_branch_ids:
                continue
            placeholders.append(
                SimpleNamespace(
                    branch=branch,
                    month=month_start,
                    invested_amount=0,
                    current_balance=0,
                    pk=None,
                )
            )
        capitals = list(base_qs)
        capitals.extend(placeholders)
        capitals.sort(
            key=lambda item: (
                (item.branch.name or "").lower() if item.branch else "",
                -(item.month.toordinal() if item.month else 0),
            )
        )
        return capitals


class PhoneCapitalCreateView(BaseCreateView):
    model = models.PhoneCapital
    form_class = PhoneCapitalUpdateForm
    template_name = "phone_capital/update.html"
    success_url_name = "phone_capital_list"

    def has_permission(self):
        return self.request.user.has_role("OWNER")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        kwargs["allow_existing"] = True
        initial = dict(kwargs.get("initial", {}))
        branch_id = self.request.GET.get("branch")
        year, month = get_request_year_month(self.request, source=self.request.path)
        if branch_id:
            initial["branch"] = branch_id
        initial["month"] = str(month)
        initial["year"] = str(year)
        kwargs["initial"] = initial
        return kwargs

    def perform_create(self, form):
        branch = form.cleaned_data.get("branch")
        month_start = form.cleaned_data.get("month_start")
        new_amount = form.cleaned_data.get("invested_amount")

        with transaction.atomic():
            capital = CapitalService.get_phone_capital(branch, month_start)
            capital.invested_amount = (capital.invested_amount or 0) + new_amount
            capital.current_balance = (capital.current_balance or 0) + new_amount
            capital.save()
            return capital

    def form_valid(self, form):
        branches = self.request.user.get_all_branches("OWNER")
        if not branches:
            branches = list(models.Branch.objects.filter(owner=self.request.user))
        branch = form.cleaned_data.get("branch")
        if not branch or branch not in branches:
            messages.error(self.request, _("Sizga bu amalni bajarish mumkin emas."))
            return redirect("dashboard")
        return super().form_valid(form)


class PhoneCapitalResetView(BaseDeleteView):
    model = models.PhoneCapital
    success_url_name = "phone_capital_list"

    def has_permission(self):
        return self.request.user.has_role("OWNER")

    def get_queryset(self):
        user = self.request.user
        branches = user.get_all_branches("OWNER")
        if not branches:
            branches = list(models.Branch.objects.filter(owner=user))
        return (
            models.PhoneCapital.objects.filter(branch__in=branches, is_deleted=False)
            .select_related("branch")
        )

    def get(self, request, *args, **kwargs):
        return redirect(reverse("phone_capital_list"))

    def post(self, request, *args, **kwargs):
        with transaction.atomic():
            capital = get_object_or_404(
                self.get_queryset().select_for_update(),
                pk=self.kwargs.get(self.pk_url_kwarg, None),
            )
            difference = capital.invested_amount
            capital.invested_amount = 0
            capital.current_balance = capital.current_balance - difference
            capital.save()
        messages.success(request, _("Kapital qayta nolga tushirildi."))
        return redirect(reverse("phone_capital_list"))
