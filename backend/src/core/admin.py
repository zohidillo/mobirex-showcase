from django.contrib import admin
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

import src.core.models as models
from src.services.support import create_admin_reply, mark_admin_read

admin.site.site_header = _("CRM boshqaruv paneli")
admin.site.site_title = _("CRM admin")
admin.site.index_title = _("Admin bo‘limi")


@admin.register(models.User)
class UserAdmin(admin.ModelAdmin):
    pass


@admin.register(models.Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display = ("id", "name")
    list_display_links = ("id", "name")


@admin.register(models.BranchUser)
class BranchUserAdmin(admin.ModelAdmin):
    pass


@admin.register(models.Phone)
class PhoneAdmin(admin.ModelAdmin):
    pass


@admin.register(models.Accessory)
class AccessoryAdmin(admin.ModelAdmin):
    pass


@admin.register(models.AccessorySale)
class AccessorySaleAdmin(admin.ModelAdmin):
    pass


@admin.register(models.PhoneCapital)
class PhoneCapitalAdmin(admin.ModelAdmin):
    pass


@admin.register(models.AccessoryCapital)
class AccessoryCapitalAdmin(admin.ModelAdmin):
    pass


@admin.register(models.Debt)
class DebtAdmin(admin.ModelAdmin):
    pass


@admin.register(models.DebtPayment)
class DebtPaymentAdmin(admin.ModelAdmin):
    pass


@admin.register(models.DebtMonthlySnapshot)
class DebtMonthlySnapshotAdmin(admin.ModelAdmin):
    pass


@admin.register(models.Expense)
class ExpenseAdmin(admin.ModelAdmin):
    pass


@admin.register(models.Salary)
class SalaryAdmin(admin.ModelAdmin):
    pass


@admin.register(models.ExtraProfit)
class ExtraProfitAdmin(admin.ModelAdmin):
    pass


@admin.register(models.Journal)
class JournalAdmin(admin.ModelAdmin):
    pass


@admin.register(models.SupportRequest)
class SupportRequestAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "request_type",
        "source",
        "status",
        "full_name",
        "phone",
        "user",
        "unread_for_admin_display",
        "last_message_at",
        "added_at",
    )
    list_filter = ("request_type", "source", "status")
    search_fields = (
        "full_name",
        "phone",
        "message",
        "user__username",
    )
    list_editable = ("status",)
    fields = (
        "user",
        "request_type",
        "source",
        "full_name",
        "phone",
        "message",
        "status",
        "admin_note",
        "metadata",
        "user_read_at",
        "admin_read_at",
        "last_message_at",
        "last_admin_reply_at",
        "last_user_message_at",
        "added_at",
        "updated_at",
    )
    readonly_fields = (
        "user",
        "request_type",
        "source",
        "full_name",
        "phone",
        "message",
        "metadata",
        "user_read_at",
        "admin_read_at",
        "last_message_at",
        "last_admin_reply_at",
        "last_user_message_at",
        "added_at",
        "updated_at",
    )
    actions = ("mark_as_read",)
    inlines = []

    def has_add_permission(self, request):
        return False

    @admin.display(boolean=True, description=_("Admin uchun yangi"))
    def unread_for_admin_display(self, obj):
        return obj.unread_for_admin

    @admin.action(description=_("O‘qilgan deb belgilash"))
    def mark_as_read(self, request, queryset):
        now = timezone.now()
        queryset.update(admin_read_at=now, updated_at=now)

    def change_view(self, request, object_id, form_url="", extra_context=None):
        if request.method == "GET":
            support_request = self.get_object(request, object_id)
            if support_request and support_request.unread_for_admin:
                mark_admin_read(support_request)
        return super().change_view(request, object_id, form_url, extra_context)

    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)
        for obj in formset.deleted_objects:
            obj.delete()
        for instance in instances:
            if isinstance(instance, models.SupportRequestMessage) and not instance.pk:
                create_admin_reply(
                    form.instance,
                    admin_user=request.user,
                    message=instance.message,
                    metadata=instance.metadata or {},
                )
            else:
                instance.save()
        formset.save_m2m()


class SupportRequestMessageInline(admin.TabularInline):
    model = models.SupportRequestMessage
    extra = 1
    can_delete = False
    fields = ("sender_type", "sender", "message", "metadata", "added_at")
    readonly_fields = ("sender", "added_at")

    def get_queryset(self, request):
        return super().get_queryset(request).filter(is_deleted=False).select_related("sender")

    def get_formset(self, request, obj=None, **kwargs):
        formset = super().get_formset(request, obj, **kwargs)
        if "sender_type" in formset.form.base_fields:
            formset.form.base_fields["sender_type"].initial = models.SupportRequestMessage.SenderType.ADMIN
        return formset


SupportRequestAdmin.inlines = [SupportRequestMessageInline]


@admin.register(models.DashboardSnapshot)
class DashboardSnapshotAdmin(admin.ModelAdmin):
    pass
