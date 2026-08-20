"""O‘zbekiston viloyatlari — yagona manba.

Qiymat (``value``) — ASCII lotin, bazada saqlanadi va API orqali qabul
qilinadi. Yorliq (``label``) — o‘zbek lotin, foydalanuvchiga ko‘rsatiladi.
Mobil ilova ro‘yxatni ``GET /api/regions/`` orqali oladi, Dart tomonida
hardcode qilinmaydi.
"""

REGION_CHOICES = [
    ("andijon", "Andijon"),
    ("buxoro", "Buxoro"),
    ("fargona", "Farg‘ona"),
    ("jizzax", "Jizzax"),
    ("xorazm", "Xorazm"),
    ("namangan", "Namangan"),
    ("navoiy", "Navoiy"),
    ("qashqadaryo", "Qashqadaryo"),
    ("qoraqalpogiston", "Qoraqalpog‘iston Respublikasi"),
    ("samarqand", "Samarqand"),
    ("sirdaryo", "Sirdaryo"),
    ("surxondaryo", "Surxondaryo"),
    ("toshkent_viloyati", "Toshkent viloyati"),
    ("toshkent_shahri", "Toshkent shahri"),
]

REGION_LABELS = dict(REGION_CHOICES)

REGION_VALUES = [value for value, _label in REGION_CHOICES]


def get_region_label(value):
    """Return the Uzbek label for a region value, or the value itself."""
    return REGION_LABELS.get(value, value or "")
