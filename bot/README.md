# CRM Support Telegram Bot

Oddiy support bot. `aiogram 3.x` bilan yozilgan.

## Funksiyalar

- `/start` bosgan odamni bazaga saqlaydi.
- 3 ta asosiy tugma beradi:
  - Dastur haqida savol berish
  - Dasturni ishlatish haqida savol
  - Ko'p beriladigan savollar
- Murojaatda F.I.O, telefon, savol so'raydi.
- Murojaatni support guruhga yuboradi.
- Guruhdagi admin bot yuborgan xabarga reply qilsa, javob mijozga boradi.
- Mijoz support javobiga reply qilsa, xabar yana support guruhga boradi.
- FAQ savol-javoblari `app/faq.py` faylida turadi.

## Ishga tushirish

### 1. Env fayl tayyorlash

```bash
cp .env.example .env
```

`.env` ichini to'ldiring:

```env
BOT_TOKEN=123456789:YOUR_BOT_TOKEN_HERE
SUPPORT_GROUP_ID=-1001234567890
DATABASE_PATH=data/support_bot.db
```

`SUPPORT_GROUP_ID` olish uchun botni guruhga qo'shing. Guruh id odatda `-100...` bilan boshlanadi.

### 2. Docker orqali ishga tushirish

```bash
docker compose up -d --build
```

Log ko'rish:

```bash
docker compose logs -f
```

To'xtatish:

```bash
docker compose down
```

## Muhim eslatmalar

Bot support guruhda xabar yubora olishi kerak. Shuning uchun botni guruhga qo'shib, admin qilish yaxshi.

Agar guruhdagi admin mijozga javob bermoqchi bo'lsa, albatta bot yuborgan murojaat xabariga `reply` qilib yozishi kerak.

Agar mijoz support bilan davomiy yozishmoqchi bo'lsa, u ham botdagi support javobiga `reply` qilib yozishi kerak.

## FAQ o'zgartirish

`app/faq.py` faylini oching:

```python
FAQ_ITEMS = [
    {
        "question": "Dastur nima?",
        "answer": "Javob matni",
    },
]
```

Shu ro'yxatga savol-javob qo'shasiz yoki o'zgartirasiz.
