# CRM

## Tarjima (i18n)

Uzbek (uz) tilidan foydalaniladi. Yangi matnlar qo‘shilganda tarjima fayllarini yangilang.

1. `DJANGO_SETTINGS_MODULE=config.settings.base python manage.py makemessages -l uz`
2. `DJANGO_SETTINGS_MODULE=config.settings.base python manage.py compilemessages`

Eslatma: `compilemessages` ishlashi uchun tizimda `gettext` (msgfmt) o‘rnatilgan bo‘lishi kerak.
